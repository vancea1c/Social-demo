from rest_framework import viewsets, permissions, filters, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from rest_framework.parsers import MultiPartParser, FormParser

from django_filters.rest_framework import DjangoFilterBackend

from channels.layers import get_channel_layer

from .models import Post, Like
from .serializers import PostDetailSerializer, PostSerializer
from Posts import serializers


def broadcast_call(post, request):
    serializer  = PostSerializer(post, context={"request": request})
    data =serializer.data
    data["action"]="post_update"
    
    channel_layer=get_channel_layer()
    
    public_payload={
        "type": "post_update",
        "data": {
            "id":             data["id"],
            "likes_count":    data["likes_count"],
            "comments_count": data.get("comments_count", 0),
            "reposts_count":  data.get("reposts_count",0),
        }
    }
    async_to_sync(channel_layer.group_send)("posts_broadcast", public_payload)
     
    private_payload ={
        "type": "post_user_update",
        "data": {
            "id" :              post.id,
            "liked_by_user":    data["liked_by_user"],
            "reposted_by_user": data["reposted_by_user"],
        }
    }
    user_group = f"posts_user_{request.user.id}"
    async_to_sync(channel_layer.group_send)(
        user_group, private_payload)

class LikeActionMixin:

    @action(detail=True, methods=["post", "delete"], url_path="like")
    def like(self, request, pk=None):
        post = self.get_object()
        if request.method == "POST":
            Like.objects.get_or_create(post=post, user=request.user)
        else:
            Like.objects.filter(post=post, user=request.user).delete()

        broadcast_call(post, request)

        return Response(
            PostSerializer(post, context={"request": request}).data,
            status=status.HTTP_200_OK
        )
    
class PostViewSet(LikeActionMixin, viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related('author', 'author__profile')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields=['type', 'parent', 'author', 'author__username']
    ordering_fields = ['created_at']
    search_fields = ['description', 'author__username']
    
    def get_queryset(self):
        user = self.request.user
        friends = user.profile.friends.all().values_list('user__id', flat=True)
        authors = list(friends) + [user.id]
        
        # pornim de la toate postările tale + ale prietenilor
        qs = Post.objects.filter(author__id__in=authors)
        
        # Găsește toți părinții postărilor din qs care nu sunt deja în qs
        parent_ids = qs.exclude(parent=None).values_list('parent', flat=True)
        # Adaugă părinții dacă nu sunt deja în queryset (de ex, dacă ai repost la un necunoscut)
        if parent_ids:
            qs = qs | Post.objects.filter(id__in=parent_ids)
            
        p_type = self.request.query_params.get("type")
        parent = self.request.query_params.get("parent")
        if p_type:
            qs = qs.filter(type=p_type)
        if parent:
            qs = qs.filter(parent=parent)
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer  # with children
        return PostSerializer 
    
    def perform_create(self, serializer):
        instance = serializer.save(author=self.request.user)
        data = PostSerializer(instance, context={"request": self.request}).data
        data["action"] = "post_create"
        async_to_sync(get_channel_layer().group_send)(
            "posts_broadcast",
            {"type": "post_create", "data": data}
        )
        
    @action(detail=True, methods=['post'], url_path='repost')
    def repost(self, request, pk=None):
        parent = self.get_object()
        user = request.user
        if parent is None:
            return Response({"error":"Cannot repost without a parent post."}, status=400)
        # căutăm dacă userul a dat deja repost la această postare
        existing = Post.objects.filter(
            author=user, parent=parent, type=Post.REPOST
        ).first()

        if existing:
            deleted_id = existing.id
            existing.delete()

            # 1) broadcast the child‐post deletion
            async_to_sync(get_channel_layer().group_send)(
                "posts_broadcast",
                {
                  "type": "post_delete",
                  "data": { "id": deleted_id }
                }
            )
            broadcast_call(parent, request)
            return Response(status=status.HTTP_200_OK)
        else:
            repost = Post.objects.create(
                author=user,
                parent=parent,
                type=Post.REPOST,
                description=""
            )
        # notify everyone about the new repost item
        payload = PostSerializer(repost, context={"request": request}).data
        payload["action"] = "post_create"
        async_to_sync(get_channel_layer().group_send)(
            "posts_broadcast",
            {"type": "post_create", "data": payload}
        )

        # update parent counts/flags
        broadcast_call(parent, request)
        return Response(
            PostSerializer(repost, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], url_path='quote', parser_classes=[MultiPartParser, FormParser])
    def quote(self, request, pk=None):
        parent = self.get_object()

        # 1) Initializezi serializerul cu datele trimise (inclusiv uploads[])
        serializer = PostSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        # 2) Salvezi exact ca în perform_create (dai author, parent, type)
        quote_post = serializer.save(
            author=request.user,
            parent=parent,
            type=Post.QUOTE,
        )

        # 3) Serializezi răspunsul (inclusiv posted_media)
        resp_data = PostSerializer(quote_post, context={'request': request}).data
        resp_data['action'] = 'post_create'

        async_to_sync(get_channel_layer().group_send)(
            "posts_broadcast",
            {"type": "post_create", "data": resp_data}
        )
        broadcast_call(parent, request)
        return Response(resp_data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        parent = self.get_object()
        print(f"[BACKEND] Creating reply. Parent id: {parent.id}, type: {parent.type}")
        user = request.user
        content = request.data.get('content', '').strip()
        reply_post = Post.objects.create(
            author=user,
            parent=parent,
            type=Post.REPLY,
            description=content
        )
        reply_data = PostSerializer(reply_post, context={"request": request}).data
        reply_data["action"] = "post_create"
        async_to_sync(get_channel_layer().group_send)(
            "posts_broadcast",
            {"type": "post_create", "data": reply_data}
        )
        broadcast_call(parent, request)
        return Response(reply_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        post_id = instance.id
        parent = instance.parent
        self.perform_destroy(instance)
        async_to_sync(get_channel_layer().group_send)(
            "posts_broadcast",
            {"type": "post_delete", "data": {"id": post_id}}
        )
        if parent is not None:
            broadcast_call(parent, request)
        return Response(status=status.HTTP_204_NO_CONTENT)
