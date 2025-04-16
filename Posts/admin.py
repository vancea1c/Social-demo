from django.contrib import admin
from django import forms
from .models import Post, Media, Comment, Like
# Register your models here.

class MediaInline(admin.StackedInline):
    model = Media
    extra = 1 
    
class CommentInlineForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = '__all__'
        widgets = {
            'likes': forms.CheckboxSelectMultiple,
        }
        
class CommentInLine(admin.StackedInline):
    model = Comment
    form = CommentInlineForm
    extra = 1
    
class LikeInLine(admin.StackedInline):
    model = Like
    extra = 1 
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [MediaInline, CommentInLine, LikeInLine]
