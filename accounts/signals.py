from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from Profile.models import Profile
from django.core.mail import send_mail
from django.db.models.signals import post_save


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        send_mail(
            f"Welcome, {instance.username}!",
            "Thank you for registering! We are happy to have you with us.",
            "social.project1907@gmail.com",
            [instance.email],
            fail_silently=False,
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
