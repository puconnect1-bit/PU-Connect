from django.conf import settings

def pwa_settings(request):
    return {
        'VAPID_PUBLIC_KEY':    getattr(settings, 'VAPID_PUBLIC_KEY', ''),
        'PAYSTACK_PUBLIC_KEY': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
    }
