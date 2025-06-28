# notifications/signals.py
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from Notifications.serializers import NotificationsSerializer
from Profile.models import Profile
from Posts.models import Post, Like
from .models import Notifications
from events.utils import send_real_time



def make_notification(recipient, actor, n_type, ct, obj_id):
    """Prepare (but don’t save) a Notifications instance."""
    return Notifications(
        to_user=recipient,
        actor=actor,
        notification_type=n_type,
        target_content_type=ct,
        target_object_id=obj_id,
    )
    
@receiver(post_save, sender=Post, dispatch_uid="notif_new_post")
def notify_friends_new_post(sender, instance, created, **kwargs):
    if not created or instance.type != Post.POST:
        return
    post_ct = ContentType.objects.get_for_model(Post)
    author  = instance.author
    friends = Profile.objects.get(user=author).friends.all()

    notifs = [
        make_notification(
            recipient=f.user,
            actor=author,
            n_type=Notifications.NEW_POST,
            ct=post_ct,
            obj_id=instance.pk
        )
        for f in friends
    ]
    with transaction.atomic():
        Notifications.objects.bulk_create(notifs)
        for notif in notifs:
            try:
                send_real_time(
                    event_type="notification_message",
                    recipient_group=f"user_{notif.to_user.id}",
                    data=NotificationsSerializer(notif).data
                )
            except Exception:
                pass
        
@receiver(post_save, sender=Post, dispatch_uid="notif_post_quote")
def notify_post_quote(sender, instance, created, **kwargs):
    if not created or instance.type != Post.QUOTE:
        return
    original = instance.parent
    if not original or original.author == instance.author:
        return
    post_ct = ContentType.objects.get_for_model(Post)
    notif = make_notification(
        recipient=original.author,
        actor=instance.author,
        n_type=Notifications.POST_QUOTE,
        ct=post_ct,
        obj_id=original.pk
    )
    with transaction.atomic():
        notif.save()
        try:
            send_real_time(
                event_type="notification_message",
                recipient_group=f"user_{notif.to_user.id}",
                data=NotificationsSerializer(notif).data
            )
        except Exception:
            pass

@receiver(post_save, sender=Post, dispatch_uid="notif_post_comment")
def notify_post_comment(sender, instance, created, **kwargs):
    if not created or instance.type != Post.REPLY:
        return
    parent = instance.parent
    if parent.author == instance.author:
        return
    post_ct = ContentType.objects.get_for_model(Post)
    notif = make_notification(
        recipient=parent.author,
        actor=instance.author,
        n_type=Notifications.POST_COMMENT,
        ct=post_ct,
        obj_id=parent.pk
    )
    with transaction.atomic():
        notif.save()
        try:
            send_real_time(
                event_type="notification_message",
                recipient_group=f"user_{notif.to_user.id}",
                data=NotificationsSerializer(notif).data
            )
        except Exception:
            pass
        
@receiver(post_save, sender=Post, dispatch_uid="notif_comment_reply")
def notify_comment_reply(sender, instance, created, **kwargs):
    if not created or instance.type != Post.REPLY or not instance.parent:
        return
    parent_reply = instance.parent
    if parent_reply.author == instance.author or parent_reply.type != Post.REPLY:
        return
    top_post = parent_reply.parent or parent_reply
    post_ct = ContentType.objects.get_for_model(Post)
    notif = make_notification(
        recipient=parent_reply.author,
        actor=instance.author,
        n_type=Notifications.COMMENT_REPLY,
        ct=post_ct,
        obj_id=top_post.pk
    )
    with transaction.atomic():
        notif.save()
        try:
            send_real_time(
                event_type="notification_message",
                recipient_group=f"user_{notif.to_user.id}",
                data=NotificationsSerializer(notif).data
            )
        except Exception:
            pass
        
@receiver(post_delete, sender=Post, dispatch_uid="notif_delete_post")
def delete_notifications_for_post(sender, instance, **kwargs):
    post_ct = ContentType.objects.get_for_model(Post)
    notifs = Notifications.objects.filter(
        target_content_type=post_ct,
        target_object_id=instance.pk
    )
    for notif in notifs:
        try:
            send_real_time(
                event_type="notification_delete",
                recipient_group=f"user_{notif.to_user.id}",
                data={"id": notif.id}
            )
        except Exception:
            pass
    notifs.delete()