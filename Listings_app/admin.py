from django.contrib import admin
from .models import Listing

# Note: Listing model is registered in Base_app/admin.py with CustomListingAdmin
# to avoid AlreadyRegistered errors during autodiscover
