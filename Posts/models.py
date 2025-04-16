from encodings.punycode import T
from enum import unique
from venv import create
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from moviepy.video.io.VideoFileClip import VideoFileClip

class Post(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
        )
    description = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.author.username}'s post on {self.created_at} "
    
    class Meta:
        ordering =['created_at']

class Media(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('video', 'Video'),
    ]
    post=models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='posted_media'
        )
    file = models.FileField(upload_to='post_media/')
    media_type = models.CharField(
        max_length=5, 
        choices=MEDIA_TYPE_CHOICES
        )
    
    def clean(self):
        if self.media_type == 'video':
            try:
                clip = VideoFileClip(self.file.path)
            except Exception as e:
                raise ValidationError (f"Your video couldn't be processed: {e}")
            
            if clip.duration > 180:
                raise ValidationError("Your video must be shorter than 3 minutes")
            
            clip.close()
        
class Like(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
        )
    liked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('post', 'user'))
        ordering = ['liked_at']
        
    def __str__(self):
        return f"{self.user.username} liked Post {self.post.pk}"
    
class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
        )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
        )
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        related_name='replies'
        )
    
    likes = models.ManyToManyField(
        User,
        related_name='comment_likes',
        blank=True
    )
    
    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.pk}"
    
    class Meta:
        ordering = ['created_at']