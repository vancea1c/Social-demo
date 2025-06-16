from rest_framework import serializers
from .models import Post, Media, Like

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['id', 'file', 'media_type']
        read_only_fields = ['id', 'media_type']

class PostSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ImageField(source='author.profile.profile_image',read_only=True)
    display_name = serializers.SerializerMethodField(read_only=True)
    username     = serializers.CharField(source='author.username', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    
    type = serializers.ChoiceField(
        choices=Post.TYPE_CHOICES,
        default=Post.POST,
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        required=False,
        allow_null=True,
    )
    
    posted_media = MediaSerializer(many=True, read_only=True)
    uploads = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        help_text="List of image/video files"
    )
    
    comments_count = serializers.SerializerMethodField(read_only=True)
    reposts_count = serializers.SerializerMethodField(read_only=True)

    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    
    liked_by_user     = serializers.SerializerMethodField(read_only=True)
    reposted_by_user  = serializers.SerializerMethodField(read_only=True)
    

    class Meta:
        model = Post
        fields = [
            'id', 'avatar_url', 'display_name', 'username',
            'created_at', 'type', 'parent', 'description',
            'posted_media',
            'uploads',
            'comments_count',
            'likes_count',
            'reposts_count', 'liked_by_user', 'reposted_by_user',
        ]
        read_only_fields = ['id']
    def get_reposts_count(self, obj):
        reposts = obj.children.filter(type=Post.REPOST).count()
        quotes  = obj.children.filter(type=Post.QUOTE).count()
        return reposts + quotes
        
    def get_comments_count(self, obj):
        return obj.children.filter(type=Post.REPLY).count()
    def get_display_name(self, obj):
        user = obj.author
        return f"{user.first_name} {user.last_name}".strip() or user.username
    
    def get_liked_by_user(self, obj):
        user= self.context['request'].user
        return obj.likes.filter(user=user).exists()
    
    def get_reposted_by_user(self, obj):
        user = self.context['request'].user
        return obj.children.filter(author=user, type=Post.REPOST).exists()

    def validate_uploads(self, files):
        MAX_FILES = 4
        MAX_VIDEO_BYTES = 256 * 1024 * 1024
        if len(files) > MAX_FILES:
            raise serializers.ValidationError(
                f"You can upload up to {MAX_FILES} media items (photos or videos)."
            )
        for f in files:
            if f.content_type.startswith("video/") and f.size > MAX_VIDEO_BYTES:
                raise serializers.ValidationError(
                    "Each video must be smaller than 256 MB."
                )

        return files
    
    def validate(self, data):
        post_type=data.get('type') or (self.instance.type if self.instance else None)
        parent = data.get('parent') if 'parent' in data else (self.instance.parent if self.instance else None)
        if post_type == 'repost' and not parent:
            raise serializers.ValidationError("A repost must have a parent post.")
        return data
    
    def create(self, validated_data):
        uploads = validated_data.pop('uploads', [])
        post = Post.objects.create(**validated_data)
        for f in uploads:
            kind = 'video' if f.content_type.startswith('video/') else 'photo'
            Media.objects.create(post=post, file=f, media_type=kind)
        return post
    
class PostDetailSerializer(PostSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        replies = obj.children.filter(type=Post.REPLY)
        return PostDetailSerializer(replies, many=True, context=self.context).data

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['children']