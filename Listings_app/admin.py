from django.contrib import admin
from .models import Listing, Wishlist

# Note: Listing model is registered in Base_app/admin.py with CustomListingAdmin
# to avoid AlreadyRegistered errors during autodiscover


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')
    list_select_related = ('user', 'listing')
    autocomplete_fields = ('user', 'listing')
    date_hierarchy = 'created_at'
