from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Q
from Notifications.serializers import NotificationsSerializer
from events.utils import send_real_time

from .models import Post, Like
from Notifications.models import Notifications
from .serializers import PostDetailSerializer, PostSerializer

POST_CT = ContentType.objects.get_for_model(Post)

def get_visible_user_ids(post):
    author_profile = post.author.profile

    if not author_profile.is_private:
        return None 

    friend_ids = list(author_profile.friends.values_list("user__id", flat=True))
    friend_ids.append(post.author.id)
    return friend_ids

def broadcast_post_create(post, request):
    """Send a post_create event to appropriate users (filtered by privacy)."""
    data = PostSerializer(post, context={"request": request}).data
    data["action"] = "post_create"

    visible_ids = get_visible_user_ids(post)

    if visible_ids is None:
        send_real_time("post_create", "events_broadcast", data)
    else:
        for uid in visible_ids:
            send_real_time("post_create", f"user_{uid}", data)

def broadcast_call(post, request):
    serializer  = PostSerializer(post, context={"request": request})
    data =serializer.data
    
    send_real_time(
      event_type="post_update",
      recipient_group="events_broadcast",
      data={
        "id":             data["id"],
        "likes_count":    data["likes_count"],
        "comments_count": data.get("comments_count", 0),
        "reposts_count":  data.get("reposts_count", 0),
      }
    )
    send_real_time(
      event_type="post_user_update",
      recipient_group=f"user_{request.user.id}",
      data={
        "id":               post.id,
        "liked_by_user":    data["liked_by_user"],
        "reposted_by_user": data["reposted_by_user"],
      }
    )

class LikeActionMixin:
    @action(detail=True, methods=["post", "delete"], url_path="like")
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        # 1) Like or Unlike logic
        if request.method == "POST":
            try:
                with transaction.atomic():
                    like, created = Like.objects.get_or_create(post=post, user=user)
            except IntegrityError:
                like = Like.objects.get(post=post, user=user)
        else:
            Like.objects.filter(post=post, user=user).delete()

        # ✅ 2) Skip notification logic entirely if self-like
        if post.author != user:
            notif_type = (
                Notifications.COMMENT_LIKE if post.type == Post.REPLY else Notifications.POST_LIKE
            )
            notif, _ = Notifications.objects.get_or_create(
                to_user=post.author,
                actor=user,
                notification_type=notif_type,
                target_content_type=POST_CT,
                target_object_id=post.id,
                defaults={"active": True},
            )

            notif_should_be_active = Like.objects.filter(post=post, user=user).exists()
            if notif.active != notif_should_be_active:
                notif.active = notif_should_be_active
                notif.save(update_fields=["active"])
                if not notif.active:
                    send_real_time(
                        event_type="notification_delete",
                        recipient_group=f"user_{notif.to_user.id}",
                        data={"id": notif.id}
                    )

            if notif.active:
                try:
                    payload = NotificationsSerializer(notif, context={"request": request}).data
                    send_real_time(
                        event_type="notification_message",
                        recipient_group=f"user_{post.author.id}",
                        data=payload,
                    )
                except Exception:
                    pass

        # 3) Always broadcast post updates
        broadcast_call(post, request)

        return Response(
            PostSerializer(post, context={"request": request}).data,
            status=status.HTTP_200_OK
        )

    
class PostViewSet(LikeActionMixin, viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related('author', 'author__profile')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields=['type', 'parent', 'author', 'author__username']
    ordering_fields = ['created_at']
    search_fields = ['description', 'author__username']

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostSerializer 
    
    
    
    def get_queryset(self):
        user = self.request.user
        profile = user.profile

        friend_ids = profile.friends.values_list("user__id", flat=True)
        visible_authors = list(friend_ids) + [user.id]

        base_qs = Post.objects.filter(
            Q(author__id__in=visible_authors) |
            Q(author__profile__is_private=False)
        )
        
        parent_ids = base_qs.exclude(parent=None).values_list("parent", flat=True)
        parents = Post.objects.filter(id__in=parent_ids)

        replies_to_visible = Post.objects.filter(
            type=Post.REPLY,
            parent__in=base_qs.values("id")
        )

        final_qs = base_qs | parents | replies_to_visible

        return final_qs.select_related("author", "author__profile").distinct().order_by("-created_at")

    
    def perform_create(self, serializer):
        instance = serializer.save(author=self.request.user)
        broadcast_post_create(instance, self.request)

        
    @action(detail=False, methods=['get'], url_path='liked')
    def liked(self, request):
        likes_qs = Like.objects.filter(user=request.user).order_by('-liked_at')
        post_ids = likes_qs.values_list('post_id', flat=True)
        qs = Post.objects.filter(pk__in=post_ids) \
                         .select_related('author', 'author__profile') \
                         .distinct()
        page = self.paginate_queryset(qs)
        serializer = PostSerializer(page or qs, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
        
    @action(detail=True, methods=['post'], url_path='repost')
    def repost(self, request, pk=None):
        post = self.get_object()
        user = request.user

        try:
            with transaction.atomic():
                repost_obj, created = Post.objects.get_or_create(
                    author=user,
                    parent=post,
                    type=Post.REPOST,
                    defaults={"description": ""},
                )
        except IntegrityError:
            repost_obj = Post.objects.get(author=user, parent=post, type=Post.REPOST)
            created = False

        if post.author != user:
            notif_type = Notifications.POST_REPOST
            notif, _ = Notifications.objects.get_or_create(
                to_user=post.author,
                actor=user,
                notification_type=notif_type,
                target_content_type=POST_CT,
                target_object_id=post.id,
                defaults={"active": True},
            )

            if created:
                if not notif.active:
                    notif.active = True
                    notif.save(update_fields=["active"])
                try:
                    payload = NotificationsSerializer(notif, context={"request": request}).data
                    send_real_time(
                        event_type="notification_message",
                        recipient_group=f"user_{post.author.id}",
                        data=payload,
                    )
                except Exception:
                    pass
            else:
                if notif.active:
                    notif.active = False
                    notif.save(update_fields=["active"])
                    send_real_time(
                                        event_type="notification_delete",
                                        recipient_group=f"user_{notif.to_user.id}",
                                        data={"id": notif.id}
                                    )

        if created:
            broadcast_post_create(repost_obj, request)
            broadcast_call(post, request)
            return Response(PostSerializer(repost_obj, context={"request": request}).data, status=status.HTTP_201_CREATED)
        else:
            repost_id = repost_obj.id
            repost_obj.delete()

            send_real_time(
                event_type="post_delete",
                recipient_group="events_broadcast",
                data={"id": repost_id}
            )
            broadcast_call(post, request)
            return Response(status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['post'], url_path='quote', parser_classes=[MultiPartParser, FormParser])
    def quote(self, request, pk=None):
        parent = self.get_object()
        serializer = PostSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        quote_post = serializer.save(
            author=request.user,
            parent=parent,
            type=Post.QUOTE,
        )
        broadcast_post_create(quote_post, request)
        broadcast_call(parent, request)
        data = PostSerializer(quote_post, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        parent = self.get_object()
        print(f"[BACKEND] Creating reply. Parent id: {parent.id}, type: {parent.type}")
        content = request.data.get('content', '').strip()
        reply_post = Post.objects.create(
            author=request.user,
            parent=parent,
            type=Post.REPLY,
            description=content
        )
        data = PostSerializer(reply_post, context={"request": request}).data
        send_real_time(
            event_type="post_create",
            recipient_group="events_broadcast",
            data=data
        )
        broadcast_call(parent, request)
        return Response(data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        post_id = instance.id
        parent = instance.parent
        self.perform_destroy(instance)
        send_real_time(
            event_type="post_delete",
            recipient_group="events_broadcast",
            data={"id": post_id}
        )
        if parent is not None:
            broadcast_call(parent, request)

        return Response(status=status.HTTP_204_NO_CONTENT)