from django.contrib import admin
from django import forms
from .models import Post, Media, Like
# Register your models here.

class MediaInline(admin.StackedInline):
    model = Media
    extra = 1 
    
class LikeInLine(admin.StackedInline):
    model = Like
    extra = 1 
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'type', 'parent_id_display', 'created_at',
    )
    list_filter = ('type', 'created_at', 'author')
    search_fields = ('author__username', 'description')
    raw_id_fields = ('parent',)
    ordering = ('-created_at',)
    
    def parent_id_display(self, obj):
        return obj.parent.id if obj.parent else "-"
    parent_id_display.short_description = 'Parent'