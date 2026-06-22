from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import SiteConfig, BoostRequest, VerificationRequest


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Platform',     {'fields': ('platform_name', 'admin_email')}),
        ('Listings',     {'fields': ('max_listing_price', 'max_listings_per_user', 'max_video_size_mb')}),
        ('Boost',        {'fields': ('boost_fee', 'boost_duration_days')}),
        ('Verification', {'fields': ('verification_fee',),
                          'description': 'Fee charged to users who apply for a Verified Student badge.'}),
        ('Moderation',   {'fields': ('report_sla_hours',)}),
    )

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display   = ('user', 'status', 'fee_paid', 'liveness_passed',
                      'docs_submitted_at', 'paid_at', 'created_at', 'reviewed_by')
    list_filter    = ('status', 'liveness_passed')
    search_fields  = ('user__username', 'user__email', 'paystack_reference')
    readonly_fields = ('user', 'fee_paid', 'paystack_reference', 'paid_at',
                       'created_at', 'student_id_number', 'docs_submitted_at',
                       'liveness_passed', 'id_photo_preview', 'selfie_preview')
    actions = ['approve_verification', 'reject_verification']
    ordering = ('-created_at',)

    fieldsets = (
        ('Applicant', {
            'fields': ('user', 'fee_paid', 'paystack_reference', 'paid_at', 'created_at'),
        }),
        ('Submitted Documents', {
            'fields': ('student_id_number', 'docs_submitted_at', 'liveness_passed', 'id_photo_preview', 'selfie_preview'),
        }),
        ('Decision', {
            'fields': ('status', 'admin_note', 'reviewed_by', 'reviewed_at'),
        }),
    )

    def id_photo_preview(self, obj):
        if obj.id_photo_url:
            return format_html(
                '<a href="{url}" target="_blank">'
                '<img src="{url}" style="max-height:220px;max-width:360px;'
                'border-radius:8px;border:1px solid #ccc"/></a>',
                url=obj.id_photo_url,
            )
        return '— not uploaded —'
    id_photo_preview.short_description = 'Student ID Photo'

    def selfie_preview(self, obj):
        if obj.selfie_url:
            liveness = ('✅ Liveness passed' if obj.liveness_passed
                        else '⚠️ Liveness NOT confirmed')
            return format_html(
                '<a href="{url}" target="_blank">'
                '<img src="{url}" style="max-height:220px;max-width:220px;'
                'border-radius:50%;border:2px solid #ccc"/></a>'
                '<br><small style="color:{"#2a7"if obj.liveness_passed else"#c33"}">{lv}</small>',
                url=obj.selfie_url, lv=liveness,
            )
        return '— not uploaded —'
    selfie_preview.short_description = 'Live Selfie'

    def approve_verification(self, request, queryset):
        updated = queryset.filter(status='docs_submitted').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'{updated} request(s) approved.')
    approve_verification.short_description = 'Approve selected (docs submitted) requests'

    def reject_verification(self, request, queryset):
        updated = queryset.exclude(status='approved').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'{updated} request(s) rejected.')
    reject_verification.short_description = 'Reject selected requests'


@admin.register(BoostRequest)
class BoostRequestAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'listing', 'status', 'fee_paid', 'paid_at', 'created_at')
    list_filter   = ('status',)
    search_fields = ('user__username', 'listing__title', 'paystack_reference')
    readonly_fields = ('user', 'listing', 'fee_paid', 'paystack_reference', 'paid_at', 'created_at')
    ordering = ('-created_at',)
