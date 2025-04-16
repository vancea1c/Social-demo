from turtle import back
from django.db import models
from django.contrib.auth.models import User
from Profile.models import Profile
from Posts.models import Comment, Post
from Friendship.models import FriendRequest
# Create your models here.

class Notifications(models.Model):
    FRIEND_REQUEST = 'friend_request'
    NEW_POST = 'new_post'
    POST_LIKE = 'post_like'
    POST_COMMENT = 'post_comment'
    COMMENT_LIKE = 'comment_like'
    COMMENT_REPLY = 'comment_reply'
    
    NOTIFICATION_TYPES = (
        (FRIEND_REQUEST, 'Friend Request'),
        (NEW_POST, 'New Post'),
        (POST_LIKE, 'Post Like'),
        (POST_COMMENT, 'Post Comment'),
        (COMMENT_LIKE, 'Comment Like'),
        (COMMENT_REPLY, 'Comment Reply'),
    )
    
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        blank=True,
        null=True
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True
        )
    friend_request = models.ForeignKey(
        FriendRequest,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
        )
    comment =models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def clean(self):
        if self.notification_type == self.NEW_POST:
            self.comment = None
        
        
        if self.notification_type == self.FRIEND_REQUEST:
            self.post = None
            self.comment = None 

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Notification for {self.to_user.username} - {self.notification_type}"