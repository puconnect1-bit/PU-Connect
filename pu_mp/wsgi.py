"""
WSGI config for pu_mp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

# Load .env file before any Django imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pu_mp.settings')

application = get_wsgi_application()
