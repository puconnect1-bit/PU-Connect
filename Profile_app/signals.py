from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Follow


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """Send push + in-app notification when someone follows you."""
    if not created:
        return

    follower = instance.follower
    followed = instance.following
    follower_name = follower.get_full_name() or follower.username

    # In-app notification
    from chat_app.models import Notification
    Notification.objects.create(
        user=followed,
        type='system',
        title=f"{follower_name} followed you",
        content=f"@{follower.username} started following you",
        link=f'/profile/{follower.username}/',
    )

    # Web Push notification
    from chat_app.signals import _send_web_push
    _send_web_push(
        user=followed,
        title=f"{follower_name} followed you",
        body=f"@{follower.username} started following you",
        url=f'/profile/{follower.username}/',
    )