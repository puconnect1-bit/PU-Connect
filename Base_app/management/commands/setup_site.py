from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
import os


class Command(BaseCommand):
    help = 'Sets the Django Sites framework domain to the production domain'

    def handle(self, *args, **kwargs):
        domain = os.environ.get('SITE_DOMAIN', 'pentvarsconnect.com')
        name = os.environ.get('SITE_NAME', 'PU-Connect')
        site, created = Site.objects.update_or_create(
            id=1,
            defaults={'domain': domain, 'name': name},
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} site: {site.domain}'))
