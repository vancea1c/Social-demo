from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FriendRequest

class FriendRequestSerializer(serializers.ModelSerializer):
    to_user = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    from_username = serializers.CharField(source='from_user.username', read_only=True)
    to_username = serializers.CharField(source='to_user.username', read_only=True)
    from_avatar = serializers.SerializerMethodField()
    to_avatar = serializers.SerializerMethodField()

    def get_from_avatar(self, obj):
        request = self.context.get('request')
        user = obj.get('from_user') if isinstance(obj, dict) else getattr(obj, 'from_user', None)
        profile = getattr(user, "profile", None)
        if profile and profile.profile_image:
            url = profile.profile_image.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_to_avatar(self, obj):
        request = self.context.get('request')
        user = obj.get('to_user') if isinstance(obj, dict) else getattr(obj, 'to_user', None)
        profile = getattr(user, "profile", None)
        if profile and profile.profile_image:
            url = profile.profile_image.url
            return request.build_absolute_uri(url) if request else url
        return None
    class Meta:
        model = FriendRequest
        fields = [
            "id",
            "from_user", "from_username", "from_avatar",
            "to_user", "to_username", "to_avatar",
            "status", "created_at", "updated_at"
        ]
        read_only_fields = ["from_user", "status", "created_at", "updated_at"]
