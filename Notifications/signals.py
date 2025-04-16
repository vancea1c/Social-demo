from email import message
from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from Friendship.models import FriendRequest
from Profile.models import Profile
from .models import Notifications
from Posts.models import Post, Like, Comment

@receiver(post_save, sender=FriendRequest)
def create_friend_request_notification(sender, instance, created, **kwargs):
    if created:
        Notifications.objects.create(
            to_user = instance.to_user,
            message = f"{instance.from_user.username} sent you a friend request.",
            notification_type = Notifications.FRIEND_REQUEST,
            friend_request = instance
        )

@receiver(post_save, sender = Post)
def notify_friends_new_post(sender, instance, created,  **kwargs):
    if created:
        author = instance.author
        author_profile = Profile.objects.get(user=author)
        friends = author_profile.friends.all()

        for friend in friends:
            Notifications.objects.create(
                to_user=friend.user,
                message=f"{author.username} has a new post.",
                notification_type = Notifications.NEW_POST,
                post = instance
        )

@receiver(post_save, sender = Like)
def notify_post_like(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        if post.author != instance.user:
            Notifications.objects.create(
                to_user=post.author,
                message = f"{instance.user.username} liked your post",
                notification_type = Notifications.POST_LIKE,
                post = post
            )

@receiver(post_save, sender = Comment)
def notify_post_comment(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        if post.author != instance.author:
            Notifications.objects.create(
                to_user=post.author,
                message = f"{instance.author.username} commented on your post.",
                notification_type = Notifications.POST_COMMENT,
                comment = instance,
                post = post
            )
            
@receiver(post_save, sender = Comment)
def notify_comment_reply(sender, instance, created, **kwargs):
    if created and instance.parent is not None:
        parent_comment = instance.parent
        if parent_comment.author != instance.author:
            Notifications.objects.create(
                to_user=parent_comment.author,
                message = f"{instance.author.username} replied to your comment on {instance.post.author.username}'s Post.",
                notification_type = Notifications.COMMENT_REPLY,
                comment = instance,
                post = instance.post
            )
        
User = get_user_model()

@receiver(m2m_changed, sender = Comment.likes.through)
def notify_comment_like(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_pk in pk_set:
            if instance.author.pk != user_pk:
                user = User.objects.get(pk=user_pk)
                Notifications.objects.create(
                    to_user=instance.author,
                    message=f"{user.username} liked your comment on {instance.post.author.username}'s Post.",
                    notification_type = Notifications.COMMENT_LIKE,
                    comment=instance,
                    post = instance.post
                )