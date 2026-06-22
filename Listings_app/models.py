
from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f"{self.title} - {self.user.username}"