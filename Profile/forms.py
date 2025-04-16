from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile












class BaseProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=50,
        required=True,
        label="Username"
    )
    class Meta:
        model = Profile
        fields = (
            "username",
            "profile_image",
            "bio",
            "name",
            
        )



class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
        'username', 'profile_image', 'bio', 'name', 'birth_date', 'friends', 'is_private'
        )