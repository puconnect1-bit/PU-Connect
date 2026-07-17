from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Message, Notification
import json


def _send_web_push(user, title, body, url='/chat/'):
    """Send a Web Push notification to all of a user's subscribed devices."""
    from .models import PushSubscription
    subs = PushSubscription.objects.filter(user=user)
    if not subs.exists():
        return
    vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    vapid_email   = getattr(settings, 'VAPID_CLAIMS_EMAIL', '')
    if not vapid_private or not vapid_email:
        return
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return
    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url,
        'icon': '/static/icons/icon-192.png',
        'badge': '/static/icons/icon-192.png',
    })
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims={'sub': f'mailto:{vapid_email}'},
                content_encoding='aes128gcm',
            )
        except WebPushException as ex:
            if ex.response is not None and ex.response.status_code in (404, 410):
                sub.delete()
        except Exception:
            pass


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if not created:
        return

    recipient = instance.conversation.participants.exclude(id=instance.sender.id).first()
    if not recipient:
        return

    preview = (
        (instance.text[:50] + '...')
        if instance.text and len(instance.text) > 50
        else instance.text or 'Sent an attachment'
    )
    sender_name = instance.sender.get_full_name() or instance.sender.username

    # 1. In-app notification (shown in the bell dropdown)
    Notification.objects.create(
        user=recipient,
        type='message',
        title=f"New message from {sender_name}",
        content=preview,
        link='/chat/',
    )

    # 2. Web Push notification (shown as OS notification)
    _send_web_push(
        user=recipient,
        title=f"New message from {sender_name}",
        body=preview,
        url='/chat/',
    )