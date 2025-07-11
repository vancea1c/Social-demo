# Generated by Django 5.1.7 on 2025-06-11 17:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Notifications', '0005_alter_notifications_comment_alter_notifications_post'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notifications',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveField(
            model_name='notifications',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='notifications',
            name='friend_request',
        ),
        migrations.RemoveField(
            model_name='notifications',
            name='message',
        ),
        migrations.RemoveField(
            model_name='notifications',
            name='post',
        ),
        migrations.AddField(
            model_name='notifications',
            name='actor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='notifications',
            name='target_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='notifications',
            name='target_object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='notifications',
            index=models.Index(fields=['to_user', 'is_read', '-created_at'], name='Notificatio_to_user_360177_idx'),
        ),
    ]
