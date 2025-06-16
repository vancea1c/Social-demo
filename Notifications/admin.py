from django.contrib import admin

from Notifications.models import Notifications


@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "to_user",
        "notification_type",
        "target_content_type",
        "target_object_id",
        "target",
        "is_read",
        "created_at",
    )
    list_filter      = ('notification_type', 'is_read')
    readonly_fields  = ('target_content_type', 'target_object_id', 'created_at')
    search_fields    = ('to_user__username', 'actor__username')