from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(source='user.username', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    
    class Meta:
        model = Profile
        fields =[
            'cover_image',
            'profile_image',
            'username',
            'name',
            'bio',
            'gender',
            'is_private',
            'date_joined',
        ]
        read_only_fields = ['gender', 'username', 'date_joined']
        extra_kwargs = {
            'bio':           {'required': False, 'allow_blank': True},
            'profile_image': {'required': False, 'allow_null': True},
            'cover_image':   {'required': False, 'allow_null': True},
            'is_private':    {'required': False},
        }
        
    def validate_cover_image(self, image):
        # validare dimensiune fișier (max 5MB)
        max_size = 5 * 1024 * 1024
        if image and image.size > max_size:
            raise serializers.ValidationError("Cover image nu poate fi mai mare de 5 MB.")
        return image
    
    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def validate_profile_image(self, image):
        # validare dimensiune fișier (max 2MB)
        max_size = 2 * 1024 * 1024
        if image and image.size > max_size:
            raise serializers.ValidationError("Imaginea de profil nu poate fi mai mare de 2 MB.")
        return image
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['name'] = f"{instance.user.first_name} {instance.user.last_name}".strip()
        return data
    
    
    def validate_bio(self, value):
        # validare lungime bio
        if value and len(value) > 500:
            raise serializers.ValidationError("Bio-ul nu poate depăși 500 de caractere.")
        return value
    
    def update(self, instance, validated_data):
        # 1) procesăm name
        name = validated_data.pop('name', None)
        
        profile = super().update(instance, validated_data)
        
        if name is not None:
            parts = name.strip().split(None, 1)
            instance.user.first_name = parts[0]
            instance.user.last_name  = parts[1] if len(parts) > 1 else ''
            instance.user.save()

        # 2) salvăm restul câmpurilor Profile (bio, li se imagine, is_private)
        return profile