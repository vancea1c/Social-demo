from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Post(models.Model):
    POST      = 'post'
    REPOST    = 'repost'
    QUOTE     = 'quote'
    REPLY     = 'reply'
    TYPE_CHOICES = [
        (POST,   'Post'),
        (REPOST, 'Repost'),
        (QUOTE,  'Quote'),
        (REPLY,  'Reply'),
    ]
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
        )
    description = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent      = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )
        # nou: tipul postării
    type        = models.CharField(
        max_length=6,
        choices=TYPE_CHOICES,
        default=POST,
    )
    def clean (self):
        super().clean()
        if self.type ==Post.REPOST and self.parent is None:
            raise ValidationError("A repost must have a parent post.")
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    

    
    def __str__(self):
        user = self.author.username
        # repost simplu (share fără comentariu)
        if self.type == Post.REPOST and self.parent:
            return f"{user} reposted #{self.parent.id}"
        # quote-repost (share + comentariu)
        if self.type == Post.QUOTE and self.parent:
            base = f"{user} quoted #{self.parent.id}"
            if self.description:
                return f"{base}: {self.description[:30]}…"
            return base
        if self.type == Post.REPLY and self.parent:
            return f"{user} replied to #{self.parent.id}"
        # postare originală
        return f"{user} posted on {self.created_at:%Y-%m-%d %H:%M}"
    class Meta:
        ordering = ['-created_at']
        

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
        super().clean()
        if self.file and self.media_type == "video" and self.file.size > 256 * 1024 * 1024:
            raise ValidationError("Video must be smaller than 256 MB.")
        if len(self.file)>4:
            raise ValidationError("You can upload up to 4 media items (photos or videos).")
        
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
