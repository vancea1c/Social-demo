from rest_framework import viewsets, permissions, filters, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from rest_framework.parsers import MultiPartParser, FormParser

from channels.layers import get_channel_layer

from .models import Post, Like
from .serializers import PostSerializer


def broadcast_to_posts(event_type: str, data: dict):
    # Guard pentru date proaste
    if not data or not isinstance(data, dict) or data is None:
        print(f"[WS] WARN: {event_type} cu data invalidă, NU trimit: {data}")
        return
    else:
        print(f"[WS] {event_type} => OK, data keys: {list(data.keys())}")
    async_to_sync(get_channel_layer().group_send)(
        "posts",
        {
            "type": event_type,
            "data": data,
        }
    )

class LikeActionMixin:

    @action(detail=True, methods=["post", "delete"], url_path="like")
    def like(self, request, pk=None):
        post = self.get_object()
        if request.method == "POST":
            Like.objects.get_or_create(post=post, user=request.user)
        else:
            Like.objects.filter(post=post, user=request.user).delete()

        # 🔧 Folosim serializer complet și trimitem datele întregi prin WS
        data = PostSerializer(post, context={"request": request}).data
        data["action"] = "post_update"
        broadcast_to_posts("post_update", data)

        return Response(data, status=status.HTTP_200_OK)
    
class PostViewSet(LikeActionMixin, viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related('author', 'author__profile')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
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

    def perform_create(self, serializer):
        instance = serializer.save(author=self.request.user)
        data = PostSerializer(instance, context={"request": self.request}).data
        data["action"] = "post_create"
        broadcast_to_posts("post_create", data)
        
    @action(detail=True, methods=['post'], url_path='repost')
    def repost(self, request, pk=None):
        parent = self.get_object()
        user = request.user

        # căutăm dacă userul a dat deja repost la această postare
        existing = Post.objects.filter(
            author=user, parent=parent, type=Post.REPOST
        ).first()

        if existing:
            id_to_delete = existing.id
            existing.delete()
            broadcast_to_posts("post_delete", {"id": id_to_delete})
            data2 = PostSerializer(parent, context={"request": request}).data
            data2["action"] = "post_update"
            broadcast_to_posts("post_update", data2)
            return Response(data2, status=status.HTTP_200_OK)
        else:
            repost = Post.objects.create(
                author=user,
                parent=parent,
                type=Post.REPOST,
                description=""
            )

        # Trimite WS NOU cu repostul (post_create)
        data = PostSerializer(repost, context={"request": request}).data
        data["action"] = "post_create"
        broadcast_to_posts("post_create", data)
        # Trimite și update la original pentru count
        data2 = PostSerializer(parent, context={"request": request}).data
        data2["action"] = "post_update"
        broadcast_to_posts("post_update", data2)
        return Response(data, status=status.HTTP_200_OK)
    
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

        # 4) Broadcast WS
        broadcast_to_posts('post_create', resp_data)

        return Response(resp_data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request, pk=None):
        parent = self.get_object()
        user = request.user
        content = request.data.get('content', '').strip()
        reply_post = Post.objects.create(
            author=user,
            parent=parent,
            type=Post.REPLY,
            description=content
        )
        reply_data = PostSerializer(reply_post, context={"request": request}).data
        parent_data = PostSerializer(parent, context={"request": request}).data
        parent_data["action"] = "post_update"
        broadcast_to_posts("post_update", parent_data)
        broadcast_to_posts("post_create", reply_data)
        return Response(reply_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        # WS broadcast: anunță toți userii să șteargă postarea
        broadcast_to_posts("post_delete", {"id": instance_id})
        return Response(status=status.HTTP_204_NO_CONTENT)
