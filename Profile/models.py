from django.db import models
from django.contrib.auth.models import User

# Create your models here.

GENDER_CHOICES =(
    ('male', 'Male'),
    ('female', 'Female')
)


class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE
        )
    bio = models.TextField(
        blank=True, 
        null=True, 
        max_length=500
        )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    birth_date = models.DateField(
        blank=True, 
        null=True
        )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        default='profile_images/default.jpg'
    )
    cover_image = models.ImageField(
        upload_to="cover_images/",
        blank=True,
        null=True
    )
    friends = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    is_private = models.BooleanField(default=False)
    blocked_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="blocked_by"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def first_name(self):
        return self.user.first_name
    
    @property
    def last_name(self):
        return self.user.last_name
    
    def __str__(self) -> str:
        return f"{self.user.username}'s Profile"
    
    class Meta:
        db_table = "Customizables"
        ordering = ['user__username']
    