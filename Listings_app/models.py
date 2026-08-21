
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Listing(models.Model):
    # Linking the listing to the user who created it
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Core Data
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    listing_type = models.CharField(max_length=20, default='product') # 'product' or 'service'
    category = models.CharField(max_length=50) # e.g. 'Electronics', 'Design'
    subcategory = models.CharField(max_length=50, blank=True)
    condition = models.CharField(max_length=50, blank=True)
    
    image_url = models.URLField(max_length=500, blank=True, default='')

    contact_for_price = models.BooleanField(default=False)
    
    # Status and Metadata
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('sold', 'Sold'),
        ('boosted', 'Boosted'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ListingReport(models.Model):
    """Report a listing for policy violations."""
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('scam', 'Scam / Fraud'),
        ('fake', 'Fake / Misleading'),
        ('prohibited', 'Prohibited Item'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('off_platform', 'Off-Platform Payment Request'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listing_reports')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id}: {self.listing.title} by @{self.reporter.username}"


class Wishlist(models.Model):
    """
    Server-side saved listings.

    A user can save a listing to their wishlist. The pair (user, listing) is
    unique so tapping the heart toggles a single row. Rows live in the default
    database (the PURouter routes all apps there).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'listing']),
            models.Index(fields=['listing']),
        ]

    def __str__(self):
        return f"{self.user.username} ♥ {self.listing.title}"
