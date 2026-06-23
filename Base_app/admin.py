from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from .models import SiteConfig, BoostRequest, VerificationRequest


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Platform',     {'fields': ('platform_name', 'admin_email', 'support_email')}),
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
    list_display   = ('user', 'status_badge', 'fee_paid', 'liveness_passed',
                      'docs_submitted_at', 'paid_at', 'expires_at', 'renewal_count',
                      'created_at', 'reviewed_by', 'action_buttons')
    list_filter    = ('status', 'liveness_passed')
    search_fields  = ('user__username', 'user__email', 'paystack_reference')
    readonly_fields = ('user', 'fee_paid', 'paystack_reference', 'paid_at',
                       'created_at', 'student_id_number', 'docs_submitted_at',
                       'liveness_passed', 'id_photo_preview', 'selfie_preview',
                       'expires_at', 'renewal_count', 'expiry_status')
    actions = ['approve_verification', 'reject_verification',
               'grant_badge_directly', 'renew_badge']
    ordering = ('-created_at',)

    fieldsets = (
        ('Applicant', {
            'fields': ('user', 'fee_paid', 'paystack_reference', 'paid_at', 'created_at'),
        }),
        ('Submitted Documents', {
            'fields': ('student_id_number', 'docs_submitted_at', 'liveness_passed',
                       'id_photo_preview', 'selfie_preview'),
        }),
        ('Decision', {
            'fields': ('status', 'admin_note', 'reviewed_by', 'reviewed_at'),
        }),
        ('Badge & Renewal', {
            'fields': ('expires_at', 'renewal_count', 'expiry_status'),
            'description': 'Badge is valid for 1 year from the date of approval.',
        }),
    )

    # ── Custom URLs for inline approve/reject/grant/renew ───────────────────
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/approve/',
                 self.admin_site.admin_view(self.approve_single),
                 name='verification_approve'),
            path('<int:pk>/reject/',
                 self.admin_site.admin_view(self.reject_single),
                 name='verification_reject'),
            path('<int:pk>/grant/',
                 self.admin_site.admin_view(self.grant_single),
                 name='verification_grant'),
            path('<int:pk>/renew/',
                 self.admin_site.admin_view(self.renew_single),
                 name='verification_renew'),
        ]
        return custom + urls

    # ── List-display columns ─────────────────────────────────────────────────
    def status_badge(self, obj):
        colours = {
            'approved':        ('#16a34a', '#dcfce7'),
            'docs_submitted':  ('#b45309', '#fef3c7'),
            'paid':            ('#1d4ed8', '#dbeafe'),
            'rejected':        ('#dc2626', '#fee2e2'),
            'pending_payment': ('#6b7280', '#f3f4f6'),
        }
        fg, bg = colours.get(obj.status, ('#6b7280', '#f3f4f6'))
        label = obj.get_status_display()
        if obj.status == 'approved' and obj.is_expired:
            fg, bg, label = '#dc2626', '#fee2e2', 'Expired'
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:12px;'
            'font-size:11px;font-weight:600;white-space:nowrap">{}</span>',
            bg, fg, label,
        )
    status_badge.short_description = 'Status'

    def action_buttons(self, obj):
        if obj.status == 'docs_submitted':
            approve_url = reverse('admin:verification_approve', args=[obj.pk])
            reject_url  = reverse('admin:verification_reject',  args=[obj.pk])
            return format_html(
                '<a href="{}" style="background:#16a34a;color:#fff;padding:3px 10px;'
                'border-radius:6px;font-size:11px;font-weight:600;margin-right:4px;'
                'text-decoration:none">Approve</a>'
                '<a href="{}" style="background:#dc2626;color:#fff;padding:3px 10px;'
                'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none">'
                'Reject</a>',
                approve_url, reject_url,
            )
        if obj.status == 'approved' and obj.is_expired:
            renew_url = reverse('admin:verification_renew', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background:#b45309;color:#fff;padding:3px 10px;'
                'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none">'
                'Renew</a>', renew_url,
            )
        if obj.status in ('pending_payment', 'paid', 'rejected'):
            grant_url = reverse('admin:verification_grant', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background:#7c3aed;color:#fff;padding:3px 10px;'
                'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none">'
                'Grant Badge</a>', grant_url,
            )
        return '—'
    action_buttons.short_description = 'Quick Action'
    action_buttons.allow_tags = True

    def expiry_status(self, obj):
        if not obj.expires_at:
            return '— not set —'
        if obj.is_expired:
            return format_html(
                '<span style="color:#dc2626;font-weight:600">Expired on {}</span>',
                obj.expires_at.strftime('%d %b %Y'),
            )
        return format_html(
            '<span style="color:#16a34a;font-weight:600">Valid until {}</span>',
            obj.expires_at.strftime('%d %b %Y'),
        )
    expiry_status.short_description = 'Expiry Status'

    # ── Document previews ────────────────────────────────────────────────────
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
            liveness = '✅ Liveness passed' if obj.liveness_passed else '⚠️ Liveness NOT confirmed'
            colour   = '#2a7' if obj.liveness_passed else '#c33'
            return format_html(
                '<a href="{url}" target="_blank">'
                '<img src="{url}" style="max-height:220px;max-width:220px;'
                'border-radius:50%;border:2px solid #ccc"/></a>'
                '<br><small style="color:{colour}">{lv}</small>',
                url=obj.selfie_url, colour=colour, lv=liveness,
            )
        return '— not uploaded —'
    selfie_preview.short_description = 'Live Selfie'

    # ── Inline single-record views ───────────────────────────────────────────
    def _back(self):
        return HttpResponseRedirect(
            reverse('admin:Base_app_verificationrequest_changelist')
        )

    def approve_single(self, request, pk):
        obj = VerificationRequest.objects.get(pk=pk)
        obj.approve(reviewed_by_user=request.user)
        messages.success(
            request,
            f'@{obj.user.username} approved. Badge valid until {obj.expires_at.strftime("%d %b %Y")}.',
        )
        return self._back()

    def reject_single(self, request, pk):
        obj = VerificationRequest.objects.get(pk=pk)
        obj.status      = 'rejected'
        obj.reviewed_at = timezone.now()
        obj.reviewed_by = request.user
        obj.save()
        messages.warning(request, f'@{obj.user.username} rejected.')
        return self._back()

    def grant_single(self, request, pk):
        obj = VerificationRequest.objects.get(pk=pk)
        obj.approve(reviewed_by_user=request.user)
        messages.success(
            request,
            f'Badge granted directly to @{obj.user.username}. Valid until {obj.expires_at.strftime("%d %b %Y")}.',
        )
        return self._back()

    def renew_single(self, request, pk):
        obj = VerificationRequest.objects.get(pk=pk)
        obj.approve(reviewed_by_user=request.user, renew=True)
        messages.success(
            request,
            f'Badge renewed for @{obj.user.username}. New expiry: {obj.expires_at.strftime("%d %b %Y")}.',
        )
        return self._back()

    # ── Bulk actions ─────────────────────────────────────────────────────────
    def approve_verification(self, request, queryset):
        count = 0
        for obj in queryset.filter(status='docs_submitted'):
            obj.approve(reviewed_by_user=request.user)
            count += 1
        self.message_user(request, f'{count} request(s) approved.')
    approve_verification.short_description = 'Approve selected (docs submitted)'

    def reject_verification(self, request, queryset):
        updated = queryset.exclude(status='approved').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'{updated} request(s) rejected.')
    reject_verification.short_description = 'Reject selected requests'

    def grant_badge_directly(self, request, queryset):
        count = 0
        for obj in queryset:
            obj.approve(reviewed_by_user=request.user)
            count += 1
        self.message_user(request, f'Badge granted directly to {count} user(s).')
    grant_badge_directly.short_description = 'Grant badge directly (bypass docs/payment)'

    def renew_badge(self, request, queryset):
        count = 0
        for obj in queryset.filter(status='approved'):
            obj.approve(reviewed_by_user=request.user, renew=True)
            count += 1
        self.message_user(request, f'{count} badge(s) renewed for 1 more year.')
    renew_badge.short_description = 'Renew badge (extend 1 year from today)'


@admin.register(BoostRequest)
class BoostRequestAdmin(admin.ModelAdmin):
    list_display   = ('id', 'user', 'listing', 'status', 'fee_paid', 'paid_at', 'created_at')
    list_filter    = ('status',)
    search_fields  = ('user__username', 'listing__title', 'paystack_reference')
    readonly_fields = ('user', 'listing', 'fee_paid', 'paystack_reference', 'paid_at', 'created_at')
    ordering = ('-created_at',)
