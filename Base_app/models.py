from django.db import models
from django.contrib.auth.models import User


class SiteConfig(models.Model):
    """Singleton table — always use id=1."""
    boost_fee = models.DecimalField(max_digits=8, decimal_places=2, default=10.00)
    boost_duration_days = models.PositiveIntegerField(default=7)
    platform_name = models.CharField(max_length=100, default='PU-Connect')
    admin_email = models.EmailField(default='admin@pu-connect.edu.gh')
    max_listing_price = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    max_video_size_mb = models.PositiveIntegerField(default=100)
    report_sla_hours = models.PositiveIntegerField(default=2)
    max_listings_per_user = models.PositiveIntegerField(default=50)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Configuration'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    verification_fee = models.DecimalField(max_digits=8, decimal_places=2, default=5.00,
        help_text='Fee (GH₵) a user must pay to apply for a Verified Student badge')

    def __str__(self):
        return f'Site Config (boost fee: GH₵{self.boost_fee})'


class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('paid',            'Paid — Awaiting Documents'),
        ('docs_submitted',  'Documents Submitted — Awaiting Review'),
        ('approved',        'Approved'),
        ('rejected',        'Rejected'),
    ]
    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_request')
    fee_paid           = models.DecimalField(max_digits=8, decimal_places=2)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    paystack_reference = models.CharField(max_length=100, blank=True, null=True, unique=True)
    paid_at            = models.DateTimeField(null=True, blank=True)
    # Documents
    student_id_number  = models.CharField(max_length=50, blank=True)
    id_photo_url       = models.URLField(max_length=500, blank=True)
    selfie_url         = models.URLField(max_length=500, blank=True)
    liveness_passed    = models.BooleanField(default=False)
    docs_submitted_at  = models.DateTimeField(null=True, blank=True)
    # Review
    admin_note         = models.TextField(blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    reviewed_at        = models.DateTimeField(null=True, blank=True)
    reviewed_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='verification_reviews')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification Request'

    def __str__(self):
        return f'Verify @{self.user.username} ({self.status})'

    @property
    def is_verified(self):
        return self.status == 'approved'


class BoostRequest(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('paid', 'Paid — Awaiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boost_requests')
    listing = models.ForeignKey('Listings_app.Listing', on_delete=models.CASCADE, related_name='boost_requests')
    fee_paid = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    paystack_reference = models.CharField(max_length=100, blank=True, unique=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='boost_reviews')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Boost #{self.id} — {self.listing.title} by @{self.user.username} ({self.status})'
