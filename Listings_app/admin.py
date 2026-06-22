from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Listing

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    # This makes the admin table much more useful
    list_display = ('title', 'user', 'price', 'category', 'is_available', 'created_at')
    list_filter = ('category', 'is_available')
    search_fields = ('title', 'description', 'user__username')