from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
import os

@receiver(post_migrate)
def update_site_domain(sender, **kwargs):
    """
    Automatically updates the Site object and cleans up SocialApp duplicates.
    """
    if sender.name == 'django.contrib.sites':
        from django.contrib.sites.models import Site
        try:
            domain = 'puconnect-jr7q.onrender.com'
            name = 'PU-Marketplace'
            site_id = getattr(settings, 'SITE_ID', 1)
            
            Site.objects.filter(id=site_id).update(domain=domain, name=name)
            if not Site.objects.filter(id=site_id).exists():
                Site.objects.create(id=site_id, domain=domain, name=name)
        except Exception:
            pass

    # Force usage of settings.py by wiping SocialApp entries from DB
    if sender.name == 'allauth.socialaccount':
        from allauth.socialaccount.models import SocialApp
        try:
            # We delete ALL google apps from the DB so that Django is FORCED
            # to use the GOOGLE_CLIENT_ID from your Render Environment Variables.
            SocialApp.objects.filter(provider='google').delete()
        except Exception:
            pass
