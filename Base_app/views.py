"""
Base App Views - Homepage, About, Help, Terms, Privacy, Safety, Admin
"""

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.conf import settings
import boto3
import uuid
import os
import json


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return redirect('auth:auth_view')


def about(request):
    """
    About Page
    GET /about/
    
    Displays:
    - Company mission and vision
    - Team information
    - History and milestones
    - Values
    """
    context = {
        'page_title': 'About PU-Marketplace',
        'page_description': 'Learn about our mission to revolutionize campus commerce.',
    }
    return render(request, 'base/about.html', context)


def help_page(request):
    """
    Help & Support Center
    GET /help/
    
    Displays:
    - FAQs
    - Getting started guide
    - Troubleshooting
    - Contact support
    """
    from .models import SiteConfig as _SC
    _cfg = _SC.get()
    context = {
        'page_title': 'Help & Support - PU-Marketplace',
        'page_description': 'Find answers to common questions and get support.',
        'support_email': _cfg.support_email,
        'faqs': [
            {
                'question': 'How do I verify my student status?',
                'answer': 'Sign up with your university email address. Our system automatically verifies your status when you use your @student.pu.edu.gh email.'
            },
            {
                'question': 'Is it safe to buy and sell here?',
                'answer': 'Yes! All users are verified students. We also provide in-app messaging, secure payment options, and a rating system to ensure safe transactions.'
            },
            {
                'question': 'How do I create a listing?',
                'answer': 'Go to your Dashboard, click "New Listing", upload photos, add a description and price. Your listing goes live immediately!'
            },
            {
                'question': 'Can I meet buyers outside campus?',
                'answer': 'We recommend meeting at designated campus locations for safety. You can arrange meetups through our in-app messaging.'
            },
            {
                'question': 'What payment methods do you support?',
                'answer': 'We support Mobile Money (Vodafone Cash, MTN Mobile Money), bank transfers, and our secure escrow system.'
            },
            {
                'question': 'How do ratings work?',
                'answer': 'After each transaction, both parties can rate each other from 1-5 stars and leave comments. This builds trust in our community.'
            },
        ]
    }
    return render(request, 'base/help.html', context)


def terms(request):
    """
    Terms & Conditions Page
    GET /terms/
    
    Displays:
    - User agreement
    - Rights and responsibilities
    - Prohibited items
    - Dispute resolution
    """
    context = {
        'page_title': 'Terms & Conditions - PU-Marketplace',
        'page_description': 'Read our terms of service and user agreement.',
    }
    return render(request, 'base/terms.html', context)


def privacy(request):
    """
    Privacy Policy Page
    GET /privacy/
    
    Displays:
    - Data collection practices
    - How data is used
    - User rights
    - Cookies and tracking
    """
    context = {
        'page_title': 'Privacy Policy - PU-Marketplace',
        'page_description': 'Learn how we protect your privacy.',
    }
    return render(request, 'base/privacy.html', context)


def safety(request):
    """
    Safety Guidelines Page
    GET /safety/
    
    Displays:
    - Safe trading tips
    - Scam warnings
    - What to avoid
    - Emergency contacts
    """
    context = {
        'page_title': 'Safety Guidelines - PU-Marketplace',
        'page_description': 'Stay safe while buying and selling on campus.',
        'safety_tips': [
            {
                'title': 'Meet in Public Places',
                'description': 'Always meet at well-known campus locations like the library, student center, or cafeteria. Never meet strangers outside campus.'
            },
            {
                'title': 'Verify Before You Trade',
                'description': 'Check the seller\'s profile, reviews, and ratings. Ask questions and request additional photos if needed.'
            },
            {
                'title': 'Use In-App Messaging',
                'description': 'Communicate through our platform, not personal phone numbers. This keeps your privacy protected.'
            },
            {
                'title': 'Inspect Items Carefully',
                'description': 'Before handing over money, thoroughly inspect the item. Check for damage, missing parts, or wear.'
            },
            {
                'title': 'Trust Your Gut',
                'description': 'If something feels wrong, walk away. There are plenty of other sellers and buyers on PU-Marketplace.'
            },
            {
                'title': 'Report Suspicious Activity',
                'description': 'See scams or harassment? Report them immediately. Our team reviews all reports and takes action.'
            },
        ]
    }
    return render(request, 'base/safety.html', context)


def browse_categories(request, category=None):
    """
    Browse by Category
    GET /categories/
    GET /categories/<category>/
    
    Displays:
    - All available categories
    - Filtered listings by category
    """
    categories = [
        {'slug': 'textbooks', 'name': 'Textbooks', 'icon': 'book-open', 'count': 245},
        {'slug': 'electronics', 'name': 'Electronics', 'icon': 'laptop', 'count': 189},
        {'slug': 'services', 'name': 'Services', 'icon': 'palette', 'count': 156},
        {'slug': 'fashion', 'name': 'Fashion', 'icon': 'shirt', 'count': 423},
        {'slug': 'furniture', 'name': 'Furniture', 'icon': 'armchair', 'count': 234},
        {'slug': 'food', 'name': 'Food & Snacks', 'icon': 'utensils', 'count': 178},
    ]
    
    context = {
        'page_title': 'Browse by Category - PU-Marketplace',
        'categories': categories,
        'selected_category': category,
    }
    return render(request, 'base/categories.html', context)


def contact(request):
    """
    Contact Us Page
    GET /contact/
    POST /contact/
    
    Displays:
    - Contact form
    - Support email
    - Response time info
    """
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # TODO: Send email and save to database
        
        context = {
            'success': True,
            'message': 'Thank you for your message. We\'ll get back to you soon!'
        }
    else:
        context = {
            'page_title': 'Contact Us - PU-Marketplace',
            'page_description': 'Get in touch with our support team.',
        }
    
    return render(request, 'base/contact.html', context)


ALLOWED_CONTENT_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
    'video': ['video/mp4', 'video/webm', 'video/quicktime'],
}
MAX_FILE_SIZES = {'image': 10 * 1024 * 1024, 'video': 100 * 1024 * 1024}  # 10 MB / 100 MB


@login_required(login_url='auth:auth_view')
def r2_presign(request):
    """
    POST /api/r2-presign/
    Body: { "filename": "photo.jpg", "content_type": "image/jpeg", "resource_type": "image" }
    Returns: { "upload_url": "...", "public_url": "..." }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    import json
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    filename = body.get('filename', '')
    content_type = body.get('content_type', '')
    resource_type = body.get('resource_type', 'image')

    if resource_type not in ALLOWED_CONTENT_TYPES:
        return JsonResponse({'error': 'Invalid resource type'}, status=400)
    if content_type not in ALLOWED_CONTENT_TYPES[resource_type]:
        return JsonResponse({'error': 'File type not allowed'}, status=400)

    ext = os.path.splitext(filename)[1].lower() or '.bin'
    key = f"media/{resource_type}s/{uuid.uuid4().hex}{ext}"

    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{settings.CF_R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.CF_R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.CF_R2_SECRET_ACCESS_KEY,
        region_name='auto',
    )

    upload_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.CF_R2_BUCKET_NAME,
            'Key': key,
            'ContentType': content_type,
        },
        ExpiresIn=300,
    )

    public_url = f"{settings.CF_R2_PUBLIC_URL.rstrip('/')}/{key}"
    return JsonResponse({'upload_url': upload_url, 'public_url': public_url})


@login_required(login_url='auth:auth_view')
def r2_upload(request):
    """
    POST /api/r2-upload/
    Multipart: file field named "file", optional field "resource_type" (default "image").

    Uploads the file server-side to R2, bypassing browser CORS restrictions on
    presigned PUTs.  Returns { "public_url": "..." }.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({'error': 'No file provided'}, status=400)

    resource_type = request.POST.get('resource_type', 'image')
    if resource_type not in ALLOWED_CONTENT_TYPES:
        return JsonResponse({'error': 'Invalid resource type'}, status=400)

    content_type = uploaded.content_type or 'application/octet-stream'
    if content_type not in ALLOWED_CONTENT_TYPES[resource_type]:
        return JsonResponse({'error': 'File type not allowed'}, status=400)

    from .models import SiteConfig
    _cfg = SiteConfig.get()
    dynamic_max = {'image': 10 * 1024 * 1024, 'video': _cfg.max_video_size_mb * 1024 * 1024}
    if uploaded.size > dynamic_max[resource_type]:
        limit_mb = 10 if resource_type == 'image' else _cfg.max_video_size_mb
        return JsonResponse({'error': f'File too large (max {limit_mb} MB)'}, status=400)

    ext = os.path.splitext(uploaded.name)[1].lower() or '.bin'
    key = f"media/{resource_type}s/{uuid.uuid4().hex}{ext}"

    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{settings.CF_R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.CF_R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.CF_R2_SECRET_ACCESS_KEY,
        region_name='auto',
    )

    try:
        s3.upload_fileobj(
            uploaded,
            settings.CF_R2_BUCKET_NAME,
            key,
            ExtraArgs={'ContentType': content_type},
        )
    except Exception as e:
        return JsonResponse({'error': f'Upload failed: {e}'}, status=500)

    public_url = f"{settings.CF_R2_PUBLIC_URL.rstrip('/')}/{key}"
    return JsonResponse({'public_url': public_url})


def serve_sw(request):
    """Serve sw.js from /sw.js so the service worker scope covers the whole origin."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    try:
        with open(sw_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('// sw not found', content_type='application/javascript', status=404)


@staff_member_required(login_url='auth:auth_view')
def admin_dashboard(request):
    return render(request, 'base/admin.html')


# ── Admin API helpers ────────────────────────────────────────────────────────

def _user_to_dict(u):
    avatar_url = ''
    faculty = ''
    try:
        p = u.profile
        avatar_url = p.avatar_url or ''
        faculty = p.faculty or ''
    except Exception:
        pass
    from Listings_app.models import Listing
    listing_count = Listing.objects.filter(user=u).count()
    return {
        'id': u.id,
        'name': u.get_full_name() or u.username,
        'username': u.username,
        'email': u.email,
        'faculty': faculty,
        'avatar_url': avatar_url,
        'joined': u.date_joined.isoformat(),
        'listings': listing_count,
        'is_active': u.is_active,
        'is_staff': u.is_staff,
        'is_superuser': u.is_superuser,
        'status': 'active' if u.is_active else 'suspended',
    }


@staff_member_required(login_url='auth:auth_view')
def admin_api_stats(request):
    from Listings_app.models import Listing
    from chat_app.models import Conversation, Message
    from django.db.models import Sum

    total_users = User.objects.count()
    active_listings = Listing.objects.filter(status='active').count()
    total_listings = Listing.objects.count()
    total_conversations = Conversation.objects.count()
    total_messages = Message.objects.count()
    suspended_users = User.objects.filter(is_active=False).count()

    # Sold listings as proxy for completed trades + GMV
    sold_qs = Listing.objects.filter(status='sold')
    total_transactions = sold_qs.count()
    total_gmv = float(sold_qs.aggregate(s=Sum('price'))['s'] or 0)

    # Reels count
    try:
        from Reels_app.models import Reel
        total_reels = Reel.objects.count()
        flagged_reels = Reel.objects.filter(status='flagged').count()
    except Exception:
        total_reels = None
        flagged_reels = None

    # Reports
    try:
        from Profile_app.models import Report
        open_reports = Report.objects.filter(status='open').count()
    except Exception:
        open_reports = 0

    # Verification requests pending review
    try:
        from .models import VerificationRequest
        pending_verifications = VerificationRequest.objects.filter(status='docs_submitted').count()
    except Exception:
        pending_verifications = 0

    return JsonResponse({
        'total_users': total_users,
        'active_listings': active_listings,
        'total_listings': total_listings,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'suspended_users': suspended_users,
        'open_reports': open_reports,
        'pending_verifications': pending_verifications,
        'total_reels': total_reels,
        'flagged_reels': flagged_reels,
        'total_transactions': total_transactions,
        'total_gmv': total_gmv,
        'avg_rating': None,
    })


@staff_member_required(login_url='auth:auth_view')
def admin_api_users(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10

    qs = User.objects.select_related('profile').order_by('-date_joined')
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'suspended':
        qs = qs.filter(is_active=False)

    total = qs.count()
    users = qs[(page - 1) * page_size: page * page_size]
    return JsonResponse({
        'total': total,
        'page': page,
        'page_size': page_size,
        'users': [_user_to_dict(u) for u in users],
    })


@staff_member_required(login_url='auth:auth_view')
def admin_api_listings(request):
    from Listings_app.models import Listing
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10

    qs = Listing.objects.select_related('user').order_by('-created_at')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(user__username__icontains=q))
    if category:
        qs = qs.filter(category__iexact=category)
    if status:
        qs = qs.filter(status__iexact=status)

    total = qs.count()
    listings = qs[(page - 1) * page_size: page * page_size]
    data = []
    for l in listings:
        data.append({
            'id': l.id,
            'title': l.title,
            'seller': l.user.username,
            'seller_id': l.user.id,
            'category': l.category,
            'price': float(l.price),
            'image_url': l.image_url or '',
            'status': l.status,
            'listing_type': l.listing_type,
            'created_at': l.created_at.isoformat(),
        })
    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'listings': data})


@staff_member_required(login_url='auth:auth_view')
def admin_api_conversations(request):
    from chat_app.models import Conversation, Message
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10
    qs = Conversation.objects.prefetch_related('participants').order_by('-updated_at')
    total = qs.count()
    convs = qs[(page - 1) * page_size: page * page_size]
    data = []
    for c in convs:
        parts = list(c.participants.values('id', 'username'))
        msg_count = c.messages.count()
        last = c.messages.last()
        data.append({
            'id': c.id,
            'participants': parts,
            'listing': c.listing.title if c.listing else None,
            'message_count': msg_count,
            'last_message': last.timestamp.isoformat() if last else None,
            'created_at': c.created_at.isoformat(),
        })
    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'conversations': data})


@staff_member_required(login_url='auth:auth_view')
@require_POST
def admin_api_user_action(request, user_id):
    try:
        data = json.loads(request.body)
        action = data.get('action')
        u = User.objects.get(id=user_id)

        if action == 'suspend':
            u.is_active = False
            u.save()
            return JsonResponse({'status': 'ok', 'message': f'@{u.username} suspended'})
        elif action == 'unsuspend':
            u.is_active = True
            u.save()
            return JsonResponse({'status': 'ok', 'message': f'@{u.username} reactivated'})
        elif action == 'make_staff':
            if not request.user.is_superuser:
                return JsonResponse({'status': 'error', 'message': 'Superuser required'}, status=403)
            u.is_staff = True
            u.save()
            return JsonResponse({'status': 'ok', 'message': f'@{u.username} is now staff'})
        elif action == 'remove_staff':
            if not request.user.is_superuser:
                return JsonResponse({'status': 'error', 'message': 'Superuser required'}, status=403)
            u.is_staff = False
            u.save()
            return JsonResponse({'status': 'ok', 'message': f'@{u.username} staff removed'})
        elif action == 'delete':
            if not request.user.is_superuser:
                return JsonResponse({'status': 'error', 'message': 'Superuser required'}, status=403)
            username = u.username
            u.delete()
            return JsonResponse({'status': 'ok', 'message': f'@{username} deleted'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required(login_url='auth:auth_view')
@require_POST
def admin_api_listing_action(request, listing_id):
    from Listings_app.models import Listing
    try:
        data = json.loads(request.body)
        action = data.get('action')
        l = Listing.objects.get(id=listing_id)

        if action == 'remove':
            l.status = 'paused'
            l.is_available = False
            l.save()
            return JsonResponse({'status': 'ok', 'message': f'Listing "{l.title}" removed'})
        elif action == 'restore':
            l.status = 'active'
            l.is_available = True
            l.save()
            return JsonResponse({'status': 'ok', 'message': f'Listing "{l.title}" restored'})
        elif action == 'delete':
            if not request.user.is_superuser:
                return JsonResponse({'status': 'error', 'message': 'Superuser required'}, status=403)
            title = l.title
            l.delete()
            return JsonResponse({'status': 'ok', 'message': f'Listing "{title}" deleted permanently'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required(login_url='auth:auth_view')
def admin_api_reports(request):
    from Profile_app.models import Report
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10

    qs = Report.objects.select_related('reporter', 'reported').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)

    total = qs.count()
    reports = qs[(page - 1) * page_size: page * page_size]
    data = []
    for r in reports:
        data.append({
            'id': r.id,
            'reporter': r.reporter.username,
            'reported': r.reported.username,
            'reason': r.get_reason_display(),
            'reason_key': r.reason,
            'details': r.details,
            'status': r.status,
            'priority': r.priority,
            'admin_note': r.admin_note,
            'submitted_at': r.created_at.isoformat(),
        })
    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'reports': data})


@staff_member_required(login_url='auth:auth_view')
@require_POST
def admin_api_report_action(request, report_id):
    from Profile_app.models import Report
    from django.utils import timezone
    try:
        data = json.loads(request.body)
        action = data.get('action')
        note = data.get('note', '').strip()
        r = Report.objects.get(id=report_id)

        if action == 'resolve':
            r.status = 'resolved'
            r.admin_note = note
            r.resolved_at = timezone.now()
            r.resolved_by = request.user
            r.save()
            return JsonResponse({'status': 'ok', 'message': 'Report resolved'})
        elif action == 'investigate':
            r.status = 'investigating'
            r.admin_note = note
            r.save()
            return JsonResponse({'status': 'ok', 'message': 'Report marked as investigating'})
        elif action == 'dismiss':
            r.status = 'resolved'
            r.admin_note = note or 'Dismissed'
            r.resolved_at = timezone.now()
            r.resolved_by = request.user
            r.save()
            return JsonResponse({'status': 'ok', 'message': 'Report dismissed'})
        elif action == 'warn':
            # Mark report resolved + note the warning
            r.status = 'resolved'
            r.admin_note = f'User warned. {note}'
            r.resolved_at = timezone.now()
            r.resolved_by = request.user
            r.save()
            return JsonResponse({'status': 'ok', 'message': f'@{r.reported.username} warned and report resolved'})
        elif action == 'ban':
            reported_user = r.reported
            reported_user.is_active = False
            reported_user.save()
            r.status = 'resolved'
            r.admin_note = f'User suspended. {note}'
            r.resolved_at = timezone.now()
            r.resolved_by = request.user
            r.save()
            return JsonResponse({'status': 'ok', 'message': f'@{reported_user.username} suspended and report resolved'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)
    except Report.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required(login_url='auth:auth_view')
def admin_api_transactions(request):
    """Transactions backed by sold listings — each sold listing = a completed trade."""
    from Listings_app.models import Listing
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10

    qs = Listing.objects.filter(status='sold').select_related('user').order_by('-created_at')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(user__username__icontains=q))

    total = qs.count()
    items = qs[(page - 1) * page_size: page * page_size]
    data = []
    for l in items:
        data.append({
            'id': f'TX-{l.id}',
            'listing_id': l.id,
            'seller': l.user.username,
            'buyer': '—',
            'item': l.title,
            'amount': float(l.price),
            'category': l.category,
            'spot': '—',
            'date': l.created_at.isoformat(),
            'status': 'completed',
        })
    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'transactions': data})


# ── Site Config ─────────────────────────────────────────────────────────────

@staff_member_required(login_url='auth:auth_view')
def admin_api_config_get(request):
    from .models import SiteConfig
    cfg = SiteConfig.get()
    return JsonResponse({
        'boost_fee': float(cfg.boost_fee),
        'boost_duration_days': cfg.boost_duration_days,
        'verification_fee': float(cfg.verification_fee),
        'platform_name': cfg.platform_name,
        'admin_email': cfg.admin_email,
        'support_email': cfg.support_email,
        'max_listing_price': float(cfg.max_listing_price),
        'max_video_size_mb': cfg.max_video_size_mb,
        'report_sla_hours': cfg.report_sla_hours,
        'max_listings_per_user': cfg.max_listings_per_user,
    })


@staff_member_required(login_url='auth:auth_view')
@require_POST
def admin_api_config_save(request):
    from .models import SiteConfig
    try:
        data = json.loads(request.body)
        cfg = SiteConfig.get()
        if 'boost_fee' in data:
            cfg.boost_fee = max(0, float(data['boost_fee']))
        if 'boost_duration_days' in data:
            cfg.boost_duration_days = max(1, int(data['boost_duration_days']))
        if 'platform_name' in data and data['platform_name'].strip():
            cfg.platform_name = data['platform_name'].strip()
        if 'admin_email' in data:
            cfg.admin_email = data['admin_email'].strip()
        if 'support_email' in data:
            cfg.support_email = data['support_email'].strip()
        if 'max_listing_price' in data:
            cfg.max_listing_price = max(0, float(data['max_listing_price']))
        if 'max_video_size_mb' in data:
            cfg.max_video_size_mb = max(1, int(data['max_video_size_mb']))
        if 'report_sla_hours' in data:
            cfg.report_sla_hours = max(1, int(data['report_sla_hours']))
        if 'max_listings_per_user' in data:
            cfg.max_listings_per_user = max(1, int(data['max_listings_per_user']))
        if 'verification_fee' in data:
            cfg.verification_fee = max(0, float(data['verification_fee']))
        cfg.save()
        return JsonResponse({'status': 'ok', 'message': 'Configuration saved'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ── Public config endpoint (boost fee for the listings page) ─────────────────

def public_config(request):
    from .models import SiteConfig
    cfg = SiteConfig.get()
    return JsonResponse({
        'boost_fee': float(cfg.boost_fee),
        'boost_duration_days': cfg.boost_duration_days,
        'support_email': cfg.support_email,
        'admin_email': cfg.admin_email,
    })


# ── Boost / Paystack ─────────────────────────────────────────────────────────

@login_required(login_url='auth:auth_view')
@require_POST
def initiate_boost_payment(request):
    """Create a Paystack transaction and return the hosted checkout URL."""
    import uuid, urllib.request as urlreq, urllib.error
    from .models import BoostRequest, SiteConfig
    from Listings_app.models import Listing

    try:
        data = json.loads(request.body)
        listing_id = int(data.get('listing_id', 0))
        listing = Listing.objects.get(id=listing_id, user=request.user)
    except Listing.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    if listing.status != 'active':
        return JsonResponse({'status': 'error', 'message': 'Only active listings can be boosted'}, status=400)

    if BoostRequest.objects.filter(listing=listing, status__in=['pending_payment', 'paid']).exists():
        return JsonResponse({'status': 'error', 'message': 'A boost request for this listing is already pending'}, status=400)

    cfg = SiteConfig.get()
    secret_key = settings.PAYSTACK_SECRET_KEY
    if not secret_key:
        return JsonResponse({'status': 'error', 'message': 'Payment not configured — contact admin'}, status=503)

    reference = f'boost-{uuid.uuid4().hex[:20]}'
    amount_kobo = int(cfg.boost_fee * 100)  # Paystack uses pesewas (GHS smallest unit)
    callback_url = request.build_absolute_uri(f'/api/boost/callback/?ref={reference}')

    payload = json.dumps({
        'email': request.user.email or f'{request.user.username}@{cfg.admin_email.split("@")[-1]}',
        'amount': amount_kobo,
        'currency': 'GHS',
        'reference': reference,
        'callback_url': callback_url,
        'metadata': {
            'listing_id': listing.id,
            'listing_title': listing.title,
            'user_id': request.user.id,
            'username': request.user.username,
        },
    }).encode()

    req = urlreq.Request(
        'https://api.paystack.co/transaction/initialize',
        data=payload,
        headers={
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urlreq.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return JsonResponse({'status': 'error', 'message': f'Paystack error: {body}'}, status=502)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Payment init failed: {e}'}, status=502)

    if not result.get('status'):
        return JsonResponse({'status': 'error', 'message': result.get('message', 'Paystack error')}, status=502)

    # Create the BoostRequest now so we can track the reference
    BoostRequest.objects.create(
        user=request.user,
        listing=listing,
        fee_paid=cfg.boost_fee,
        paystack_reference=reference,
        status='pending_payment',
    )

    return JsonResponse({
        'status': 'ok',
        'authorization_url': result['data']['authorization_url'],
        'reference': reference,
    })


def paystack_callback(request):
    """Redirect target after Paystack checkout. Verifies the transaction."""
    import urllib.request as urlreq
    from .models import BoostRequest
    from django.utils import timezone
    from django.shortcuts import redirect

    reference = request.GET.get('ref', '')
    if not reference:
        return redirect('/listings/?boost=error')

    secret_key = settings.PAYSTACK_SECRET_KEY
    req = urlreq.Request(
        f'https://api.paystack.co/transaction/verify/{reference}',
        headers={'Authorization': f'Bearer {secret_key}'},
    )
    try:
        with urlreq.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
    except Exception:
        return redirect('/listings/?boost=error')

    if result.get('status') and result['data'].get('status') == 'success':
        try:
            br = BoostRequest.objects.get(paystack_reference=reference)
            if br.status == 'pending_payment':
                br.status = 'paid'
                br.paid_at = timezone.now()
                br.save()
        except BoostRequest.DoesNotExist:
            pass
        return redirect('/listings/?boost=success')

    return redirect('/listings/?boost=failed')


@csrf_exempt
def paystack_webhook(request):
    """Server-to-server Paystack event — backup confirmation."""
    import hashlib, hmac
    from .models import BoostRequest
    from django.utils import timezone

    sig = request.headers.get('X-Paystack-Signature', '')
    secret_key = settings.PAYSTACK_SECRET_KEY
    computed = hmac.new(secret_key.encode(), request.body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(sig, computed):
        return HttpResponse(status=400)

    try:
        event = json.loads(request.body)
    except Exception:
        return HttpResponse(status=400)

    if event.get('event') == 'charge.success':
        reference = event['data'].get('reference', '')
        if reference.startswith('boost-'):
            try:
                br = BoostRequest.objects.get(paystack_reference=reference)
                if br.status == 'pending_payment':
                    br.status = 'paid'
                    br.paid_at = timezone.now()
                    br.save()
            except BoostRequest.DoesNotExist:
                pass

    return HttpResponse(status=200)


@staff_member_required(login_url='auth:auth_view')
def admin_api_boosts(request):
    from .models import BoostRequest
    status = request.GET.get('status', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10

    qs = BoostRequest.objects.select_related('user', 'listing').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    else:
        # By default hide pending_payment (not yet paid) from admin queue
        qs = qs.exclude(status='pending_payment')

    total = qs.count()
    items = qs[(page - 1) * page_size: page * page_size]
    data = []
    for b in items:
        data.append({
            'id': b.id,
            'listing_id': b.listing.id,
            'listing_title': b.listing.title,
            'listing_image': b.listing.image_url or '',
            'username': b.user.username,
            'user_id': b.user.id,
            'fee_paid': float(b.fee_paid),
            'status': b.status,
            'admin_note': b.admin_note,
            'created_at': b.created_at.isoformat(),
            'paid_at': b.paid_at.isoformat() if b.paid_at else None,
        })
    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'boosts': data})


@staff_member_required(login_url='auth:auth_view')
@require_POST
def admin_api_boost_action(request, boost_id):
    from .models import BoostRequest
    from django.utils import timezone
    try:
        data = json.loads(request.body)
        action = data.get('action')
        note = data.get('note', '').strip()
        b = BoostRequest.objects.select_related('listing').get(id=boost_id)

        if action == 'approve':
            b.status = 'approved'
            b.admin_note = note
            b.reviewed_at = timezone.now()
            b.reviewed_by = request.user
            b.save()
            # Activate the listing as boosted
            b.listing.status = 'boosted'
            b.listing.is_available = True
            b.listing.save()
            return JsonResponse({'status': 'ok', 'message': f'Boost approved — "{b.listing.title}" is now featured'})
        elif action == 'reject':
            b.status = 'rejected'
            b.admin_note = note or 'Rejected by admin'
            b.reviewed_at = timezone.now()
            b.reviewed_by = request.user
            b.save()
            return JsonResponse({'status': 'ok', 'message': f'Boost request rejected'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)
    except BoostRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Boost request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required(login_url='auth:auth_view')
def admin_api_verifications(request):
    from .models import VerificationRequest
    status = request.GET.get('status', '')
    page = max(1, int(request.GET.get('page', 1)))
    page_size = 10

    qs = VerificationRequest.objects.select_related('user').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)

    total = qs.count()
    items = qs[(page - 1) * page_size: page * page_size]
    data = []
    for v in items:
        data.append({
            'id': v.id,
            'username': v.user.username,
            'name': v.user.get_full_name() or v.user.username,
            'email': v.user.email,
            'status': v.status,
            'fee_paid': float(v.fee_paid) if v.fee_paid else 0,
            'liveness_passed': v.liveness_passed,
            'student_id_number': v.student_id_number or '',
            'id_photo_url': v.id_photo_url or '',
            'selfie_url': v.selfie_url or '',
            'admin_note': v.admin_note or '',
            'docs_submitted_at': v.docs_submitted_at.isoformat() if v.docs_submitted_at else None,
            'paid_at': v.paid_at.isoformat() if v.paid_at else None,
            'created_at': v.created_at.isoformat(),
            'expires_at': v.expires_at.isoformat() if v.expires_at else None,
        })
    return JsonResponse({'total': total, 'page': page, 'page_size': page_size, 'verifications': data})


@staff_member_required(login_url='auth:auth_view')
@require_POST
def admin_api_verification_action(request, verification_id):
    from .models import VerificationRequest
    from django.utils import timezone
    from datetime import timedelta
    try:
        data = json.loads(request.body)
        action = data.get('action')
        note = data.get('note', '').strip()
        v = VerificationRequest.objects.select_related('user').get(id=verification_id)

        if action == 'approve':
            if v.status not in ('docs_submitted', 'paid', 'rejected'):
                return JsonResponse({'status': 'error', 'message': f'Cannot approve from status: {v.status}'}, status=400)
            v.status = 'approved'
            v.admin_note = note
            v.reviewed_at = timezone.now()
            v.reviewed_by = request.user
            v.expires_at = timezone.now() + timedelta(days=365)
            v.save()
            return JsonResponse({'status': 'ok', 'message': f'@{v.user.username} verification approved'})
        elif action == 'reject':
            if v.status == 'approved':
                return JsonResponse({'status': 'error', 'message': 'Cannot reject an already-approved badge'}, status=400)
            v.status = 'rejected'
            v.admin_note = note or 'Rejected by admin'
            v.reviewed_at = timezone.now()
            v.reviewed_by = request.user
            v.save()
            return JsonResponse({'status': 'ok', 'message': f'@{v.user.username} verification rejected'})
        elif action == 'grant':
            v.status = 'approved'
            v.admin_note = note or 'Badge granted directly by admin'
            v.reviewed_at = timezone.now()
            v.reviewed_by = request.user
            v.expires_at = timezone.now() + timedelta(days=365)
            v.save()
            return JsonResponse({'status': 'ok', 'message': f'Badge granted to @{v.user.username}'})
        elif action == 'renew':
            if v.status != 'approved':
                return JsonResponse({'status': 'error', 'message': 'Can only renew approved badges'}, status=400)
            v.expires_at = timezone.now() + timedelta(days=365)
            v.renewal_count = (v.renewal_count or 0) + 1
            v.admin_note = note or f'Renewed by admin (renewal #{v.renewal_count})'
            v.reviewed_at = timezone.now()
            v.reviewed_by = request.user
            v.save()
            return JsonResponse({'status': 'ok', 'message': f'Badge renewed for @{v.user.username}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)
    except VerificationRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Verification request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def serve_offline(request):
    """Offline fallback page served by the service worker."""
    return render(request, 'base/offline.html')
