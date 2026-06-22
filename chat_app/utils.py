import json
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import PushSubscription

def send_web_push(user, title, message, link=None):
    """Sends a Web Push notification to all active subscriptions of the user."""
    subscriptions = PushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        return
        
    payload = {
        'title': title,
        'body': message,
        'icon': '/static/icons/logo-192.png',
        'badge': '/static/icons/logo-192.png',
        'data': {
            'url': link or '/dashboard/dashboard/'
        }
    }
    
    payload_str = json.dumps(payload)
    
    for sub in subscriptions:
        try:
            subscription_info = {
                'endpoint': sub.endpoint,
                'keys': {
                    'auth': sub.auth,
                    'p256dh': sub.p256dh
                }
            }
            webpush(
                subscription_info=subscription_info,
                data=payload_str,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=settings.VAPID_CLAIMS,
                ttl=86400  # 1 day TTL
            )
        except WebPushException as ex:
            # 404 or 410 means subscription is no longer valid
            if ex.response is not None and ex.response.status_code in [404, 410]:
                sub.delete()
        except Exception as e:
            print(f"Error sending push notification to subscription {sub.id}: {e}")
