from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing


@receiver(post_save, sender=Listing)
def create_listing_notification(sender, instance, created, **kwargs):
    """Send push + in-app notification when a user creates a new listing."""
    if not created:
        return

    user = instance.user
    # In-app notification for the listing owner (confirmation)
    from chat_app.models import Notification
    Notification.objects.create(
        user=user,
        type='system',
        title='Listing created successfully',
        content=f'Your listing "{instance.title}" is now live',
        link=f'/listings/{instance.id}/',
    )

    # Web Push notification to the listing owner
    from chat_app.signals import _send_web_push
    _send_web_push(
        user=user,
        title='Listing created successfully',
        body=f'Your listing "{instance.title}" is now live',
        url=f'/listings/{instance.id}/',
    )


def send_listing_report_notifications(report):
    """Send push + in-app notification to all admins about a listing report."""
    from chat_app.models import Notification
    from chat_app.signals import _send_web_push
    from django.contrib.auth.models import User

    admins = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
    for admin in admins.distinct():
        Notification.objects.create(
            user=admin,
            type='system',
            title='Listing reported',
            content=f'@{report.reporter.username} reported "{report.listing.title}" for {report.get_reason_display()}',
            link=f'/listings/{report.listing.id}/',
        )
        _send_web_push(
            user=admin,
            title='Listing reported',
            body=f'@{report.reporter.username} reported "{report.listing.title}" for {report.get_reason_display()}',
            url=f'/listings/{report.listing.id}/',
        )