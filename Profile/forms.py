from dataclasses import fields
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    name = forms.CharField(label="Name", max_length=150, required=False)
    
    class Meta:
        model = Profile
        fields =[
            'cover_image',
            'profile_image',
            'name',
            'bio',
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize “name” din user.first_name + user.last_name
        user = getattr(self.instance, 'user', None)
        if user:
            full = f"{user.first_name} {user.last_name}".strip()
            self.fields['name'].initial = full
            
    def save(self, commit=True):
        # salvăm profile fără commit
        profile = super().save(commit=False)
        # spargem “name” în prenume + nume de familie
        name = self.cleaned_data.get('name', '').strip()
        if name:
            parts = name.split(None, 1)
            profile.user.first_name = parts[0]
            profile.user.last_name  = parts[1] if len(parts) > 1 else ''
        else:
            profile.user.first_name = ''
            profile.user.last_name  = ''
        # commit dacă trebuie
        if commit:
            profile.user.save()
            profile.save()
            self.save_m2m()
        return profile