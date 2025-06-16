from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class FriendRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friend_requests_sent'
        )
    to_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friend_requests_received'
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    active = models.BooleanField(default=True, db_index=True)
    def clean(self):
        if self.from_user == self.to_user:
            raise ValidationError("You cannot send a friend request to yourself.")
        
        if FriendRequest.objects.filter(
            from_user=self.to_user,
            to_user=self.from_user,
            active=True
        ).exists():
            raise ValidationError("This user has already sent you a friend request.")
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"
    class Meta:
        ordering = ['created_at']
        unique_together = ('from_user', 'to_user')