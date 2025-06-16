from rest_framework import serializers
from rest_framework.reverse import reverse

from Posts.models import Post

from .models import Notifications


class NotificationsSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.username', read_only=True)
    actor_avatar = serializers.SerializerMethodField()
    target_type = serializers.CharField(source='target_content_type.model', read_only=True)
    target_id = serializers.IntegerField(source='target_object_id', read_only=True)
    message = serializers.CharField(read_only=True)
    parent_post_id = serializers.SerializerMethodField()
    class Meta:
        model = Notifications
        fields = [
            'id', 'actor', 'actor_avatar', 'notification_type', 'message',
            'target_type', 'target_id',"parent_post_id",
            'created_at', 'is_read', 'active',
        ]
        read_only_fields = [
            'id', 'actor', 'actor_avatar', 'message',
            'target_type', 'target_id', 'created_at',
        ]

    def get_actor_avatar(self, obj):
        request = self.context.get('request')
        avatar = getattr(obj.actor.profile, 'profile_image', None)
        if avatar and hasattr(avatar, 'url') and request:
            return request.build_absolute_uri(avatar.url)
        return None
    def get_parent_post_id(self, obj):
        if obj.target_content_type.model == "post":
            try:
                post = Post.objects.get(id=obj.target_object_id)
                return post.parent.id if post.parent else post.id
            except Post.DoesNotExist:
                return None
        return None

