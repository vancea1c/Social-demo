from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User

class Notifications(models.Model):  # renamed to singular
    NEW_POST       = 'new_post'
    POST_LIKE      = 'post_like'
    POST_COMMENT   = 'post_comment'
    COMMENT_LIKE   = 'comment_like'
    COMMENT_REPLY  = 'comment_reply'
    POST_REPOST    = 'post_repost'
    POST_QUOTE     = 'post_quote'

    NOTIFICATION_TYPES = (
        (NEW_POST,       'New Post'),
        (POST_LIKE,      'Post Like'),
        (POST_COMMENT,   'Post Comment'),
        (COMMENT_LIKE,   'Comment Like'),
        (COMMENT_REPLY,  'Comment Reply'),
        (POST_REPOST,    'Post Repost'),
        (POST_QUOTE,     'Post Quote'),
    )

    to_user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)

    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id    = models.PositiveIntegerField()
    target              = GenericForeignKey('target_content_type', 'target_object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)
    active = models.BooleanField(default=True, db_index=True)

    @property
    def message(self):
        templates = {
            self.NEW_POST:       "{actor} made a new post.",
            self.POST_LIKE:      "{actor} liked your post.",
            self.POST_COMMENT:   "{actor} commented on your post.",
            self.COMMENT_LIKE:   "{actor} liked your comment.",
            self.COMMENT_REPLY:  "{actor} replied to your comment.",
            self.POST_REPOST:    "{actor} reposted your post.",
            self.POST_QUOTE:     "{actor} quoted your post.",
        }
        return templates[self.notification_type].format(actor=self.actor.username if self.actor else "Someone")

    def __str__(self):
        return f"{self.notification_type} → {self.to_user.username}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', 'is_read', '-created_at']),
            models.Index(fields=['to_user', 'active', '-created_at']),
        ]