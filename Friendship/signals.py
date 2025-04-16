from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FriendRequest
from Profile.models import Profile

@receiver(post_save, sender = FriendRequest)
def update_friends_on_accept(sender, instance, **kwrags):
    if instance.status == FriendRequest.STATUS_ACCEPTED:
        from_profile = instance.from_user.profile
        to_profile = instance.to_user.profile
        from_profile.friends.add(to_profile)
        to_profile.friends.add(from_profile)