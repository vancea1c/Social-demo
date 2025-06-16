from operator import imod
from django.contrib import admin
from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Profile

# Register your models here.

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["friends"]
        widgets = {
            "friends" : forms.SelectMultiple(attrs={'size': 10})
        }




@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", 'display_friends')
    
    
    readonly_fields = ['user']
    
    filter_vertical = ("friends",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'friends':
            obj_id = request.resolver_match.kwargs.get('object_id')
            kwargs['queryset'] = Profile.objects.exclude(id=obj_id) 
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def display_friends(self, user):
        return user.friends.count() 
    
    def has_add_permission(self, request): 
        return False
    
    display_friends.short_description = "Friends"