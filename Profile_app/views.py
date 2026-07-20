import django
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile, Follow
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.utils import timezone

from django.contrib import messages
from Listings_app.models import Listing
from chat_app.signals import _send_web_push
from chat_app.models import Notification
import json



# Create your views here.

@never_cache

@login_required(login_url='auth:auth_view')
def profile(request):
    """
    User Profile Page
    GET /profile/
    
    Displays:
    - User profile information
    - Avatar and basic details
    - Reputation and ratings
    - Activity history
    - Link to profile settings
    """
    context = {
        'page_title': 'My Profile - PU-Marketplace',
        'page_description': 'View and manage your profile information.',
        # Add any additional context data needed for the profile page here
    }
    return render(request, 'profile/profile.html', context)

@login_required(login_url='auth:auth_view')
def settings(request):
    """
    Profile Settings Page
    GET /profile/settings/
    
    Displays:
    - Account settings
    - Privacy settings
    - Notification preferences
    - Security settings
    """
    context = {
        'page_title': 'Settings - PU-Marketplace',
        'page_description': 'Manage your account settings.',
    }
    return render(request, 'profile/settings.html', context)





def _get_verified_status(user):
    from Base_app.models import user_is_verified
    return user_is_verified(user)

def _get_verification_status(user):
    try:
        return user.verification_request.status
    except Exception:
        return None


@login_required(login_url='auth:auth_view')
@never_cache
def get_my_profile(request):
    """Sends DB data to the frontend on load."""
    from Listings_app.models import Listing

    profile, _ = Profile.objects.get_or_create(user=request.user)
    user = request.user

    listing_qs = Listing.objects.filter(user=user)
    active_listings = list(
        listing_qs.filter(status__in=['active', 'boosted'])
        .order_by('-created_at')[:12]
        .values('id', 'title', 'price', 'image_url', 'listing_type', 'status', 'contact_for_price')
    )
    # Serialise Decimal -> str for JSON
    for l in active_listings:
        l['price'] = str(l['price'])

    return JsonResponse({
        'username': user.username,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'bio': profile.bio or "",
        'faculty': profile.faculty or "",
        'location': profile.location or "",
        'phone': profile.phone or "",
        'avatarSrc': profile.avatar_url or "",
        'bannerSrc': profile.banner_url or "",
        'joined': user.date_joined.strftime('%B %Y'),
        'is_verified': _get_verified_status(user),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'verification_status': _get_verification_status(user),
        'listing_count': listing_qs.count(),
        'sold_count': listing_qs.filter(status='sold').count(),
        'followers_count': user.followers_set.count(),
        'following_count': user.following_set.count(),
        'active_listings': active_listings,
    })
  

from .forms import PhoneForm, ProfileSetupForm

@login_required(login_url='auth:auth_view')
def complete_profile(request):
    """
    AJAX POST  — called by the setup modal on the dashboard.
    GET        — returns whether the profile still needs completing (for the modal trigger).
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user = request.user

    needs_setup = not (profile.phone and profile.faculty)

    if request.method == 'GET':
        return JsonResponse({
            'needs_setup': needs_setup,
            'name': user.get_full_name(),
            'username': user.username,
        })

    # POST — modal form submission (JSON)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    form = ProfileSetupForm(data, initial={'user_pk': user.pk})
    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({'status': 'error', 'message': first_error}, status=400)

    # Save name + username to User
    full_name = form.cleaned_data['name'].strip()
    parts = full_name.split(' ', 1)
    user.first_name = parts[0]
    user.last_name = parts[1] if len(parts) > 1 else ''
    user.username = form.cleaned_data['username']
    user.save()

    # Save phone + faculty to Profile
    profile.phone = form.cleaned_data['phone']
    profile.faculty = form.cleaned_data['faculty']
    profile.save()

    return JsonResponse({'status': 'success'})









@login_required(login_url='auth:auth_view')
@require_POST
def update_profile_api(request):
    """Receives data and R2 links to save in DB."""
    try:
        data = json.loads(request.body)
        user = request.user
        p, _ = Profile.objects.get_or_create(user=user)
        
        # 1. Update User model (Username & Full Name)
        new_un = data.get('username', '').strip().replace('@','')
        if new_un and new_un != user.username:
            from django.contrib.auth.models import User
            if User.objects.filter(username=new_un).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already taken'}, status=400)
            user.username = new_un
            
        full_name = data.get('name', '').strip()
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        
        user.save()

        # 2. Update Profile model
        p.bio = data.get('bio', '')
        p.faculty = data.get('faculty', '')
        p.location = data.get('location', '')
        raw_phone = data.get('phone', '').strip()
        if raw_phone:
            import re as _re
            _d = _re.sub(r'\D', '', raw_phone)
            if _d.startswith('233'): _d = _d[3:]
            elif _d.startswith('0'): _d = _d[1:]
            if len(_d) != 9:
                return JsonResponse({'status': 'error', 'message': 'Enter a valid Ghanaian number (9 digits after +233).'}, status=400)
            raw_phone = f'+233{_d}'
        p.phone = raw_phone
        if data.get('avatarSrc'):
            p.avatar_url = data.get('avatarSrc')
        if data.get('bannerSrc'):
            p.banner_url = data.get('bannerSrc')
        p.save()
        
        return JsonResponse({'status': 'success', 'username': user.username})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# Ensure your Listing model is imported


def public_profile_page(request, username):
    """Renders the public profile page for any user."""
    target = get_object_or_404(User, username=username, is_active=True)
    return render(request, 'profile/public_profile.html', {'target_username': username})


@never_cache
def public_profile_api(request, username):
    """JSON data for a public profile."""
    target = get_object_or_404(User, username=username, is_active=True)
    try:
        p = target.profile
    except Exception:
        p = None

    listing_qs = Listing.objects.filter(user=target, status__in=['active', 'boosted']).order_by('-created_at')
    active_listings = list(
        listing_qs[:12].values('id', 'title', 'price', 'image_url', 'listing_type', 'status', 'contact_for_price')
    )
    for l in active_listings:
        l['price'] = str(l['price'])

    is_following = False
    follows_you  = False
    is_own       = False
    if request.user.is_authenticated:
        is_own       = request.user == target
        is_following = Follow.objects.filter(follower=request.user, following=target).exists()
        follows_you  = Follow.objects.filter(follower=target, following=request.user).exists()

    from Base_app.models import user_is_verified
    return JsonResponse({
        'username':        target.username,
        'name':            target.get_full_name() or target.username,
        'bio':             (p.bio if p else '') or '',
        'faculty':         (p.faculty if p else '') or '',
        'location':        (p.location if p else '') or '',
        'avatarSrc':       (p.avatar_url if p else '') or '',
        'joined':          target.date_joined.strftime('%B %Y'),
        'posts_count':     listing_qs.count(),
        'followers_count': target.followers_set.count(),
        'following_count': target.following_set.count(),
        'is_following':    is_following,
        'follows_you':     follows_you,
        'is_own':          is_own,
        'is_verified':     user_is_verified(target),
        'active_listings': active_listings,
    })


@login_required(login_url='auth:auth_view')
@require_POST
def toggle_follow(request, username):
    """Toggle follow/unfollow. Returns new state."""
    target = get_object_or_404(User, username=username, is_active=True)
    if target == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot follow yourself'}, status=400)

    follow_obj, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow_obj.delete()
        is_following = False
    else:
        is_following = True

    return JsonResponse({
        'following':       is_following,
        'followers_count': target.followers_set.count(),
    })


@login_required(login_url='auth:auth_view')
@require_POST
def report_user(request, username):
    """POST /profile/<username>/report/ — submit a user report."""
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot report yourself'}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    reason = data.get('reason', '').strip()
    details = data.get('details', '').strip()
    valid_reasons = {'spam', 'scam', 'harassment', 'fake', 'inappropriate', 'other'}
    if reason not in valid_reasons:
        return JsonResponse({'status': 'error', 'message': 'Invalid reason'}, status=400)
    from .models import Report
    if Report.objects.filter(reporter=request.user, reported=target, status='open').exists():
        return JsonResponse({'status': 'error', 'message': 'You already have an open report against this user'}, status=400)
    priority = 'high' if reason in ('scam', 'harassment') else 'medium'
    report = Report.objects.create(
        reporter=request.user,
        reported=target,
        reason=reason,
        details=details,
        priority=priority,
    )
    # Notify all superusers/staff about the report
    from django.contrib.auth.models import User as StaffUser
    admins = StaffUser.objects.filter(is_superuser=True) | StaffUser.objects.filter(is_staff=True)
    for admin in admins.distinct():
        Notification.objects.create(
            user=admin,
            type='system',
            title='New user report',
            content=f'@{request.user.username} reported @{target.username} for {reason}',
            link=f'/admin/Profile_app/report/{report.id}/change/',
        )
        _send_web_push(
            user=admin,
            title='New user report',
            body=f'@{request.user.username} reported @{target.username} for {reason}',
            url='/admin/Profile_app/report/',
        )
    return JsonResponse({'status': 'success', 'message': 'Report submitted. Our team will review it shortly.'})


@login_required(login_url='auth:auth_view')
@never_cache
@login_required(login_url='auth:auth_view')
def verification_page(request):
    """Dedicated full-page student verification flow."""
    from Base_app.models import SiteConfig
    config = SiteConfig.get()
    status = _get_verification_status(request.user)
    return render(request, 'profile/verify.html', {
        'verification_fee': config.verification_fee,
        'verification_status': status,
    })


@login_required(login_url='auth:auth_view')
def verification_info(request):
    """GET — returns fee and current status for the logged-in user."""
    from Base_app.models import SiteConfig
    config = SiteConfig.get()
    status = _get_verification_status(request.user)
    return JsonResponse({
        'fee': str(config.verification_fee),
        'status': status,
        'is_verified': status == 'approved',
    })


@login_required(login_url='auth:auth_view')
@require_POST
def verification_apply(request):
    """POST — create or update a pending verification request (before payment)."""
    from Base_app.models import SiteConfig, VerificationRequest
    config = SiteConfig.get()
    vr, created = VerificationRequest.objects.get_or_create(
        user=request.user,
        defaults={'fee_paid': config.verification_fee, 'status': 'pending_payment'},
    )
    if not created and vr.status == 'approved':
        return JsonResponse({'status': 'error', 'message': 'Already verified'}, status=400)
    if not created and vr.status in ('pending_payment', 'rejected'):
        vr.fee_paid = config.verification_fee
        vr.status = 'pending_payment'
        vr.save(update_fields=['fee_paid', 'status'])
    return JsonResponse({'status': 'ok', 'fee': str(config.verification_fee), 'vr_id': vr.pk})


@login_required(login_url='auth:auth_view')
@require_POST
def verification_paid(request):
    """POST — called after Paystack confirms payment; marks as paid, awaiting documents."""
    from Base_app.models import VerificationRequest
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    ref = data.get('reference', '').strip()
    if not ref:
        return JsonResponse({'status': 'error', 'message': 'No reference'}, status=400)
    try:
        vr = VerificationRequest.objects.get(user=request.user)
    except VerificationRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No pending request'}, status=400)
    if vr.status == 'approved':
        return JsonResponse({'status': 'already_verified'})
    vr.status = 'paid'
    vr.paystack_reference = ref
    vr.paid_at = timezone.now()
    vr.save(update_fields=['status', 'paystack_reference', 'paid_at'])
    return JsonResponse({'status': 'ok'})


@login_required(login_url='auth:auth_view')
@require_POST
def verification_submit_docs(request):
    """POST — receives R2 URLs for ID photo + selfie, sets status to docs_submitted."""
    from Base_app.models import VerificationRequest
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    student_id_number = data.get('id_number', '').strip()
    id_photo_url      = data.get('id_photo_url', '').strip()
    selfie_url        = data.get('selfie_url', '').strip()
    liveness_passed   = bool(data.get('liveness_passed', False))

    if not student_id_number or not id_photo_url or not selfie_url:
        return JsonResponse({'status': 'error', 'message': 'Student ID number, ID photo and selfie are all required'}, status=400)

    try:
        vr = VerificationRequest.objects.get(user=request.user)
    except VerificationRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'No verification request found'}, status=400)

    if vr.status == 'approved':
        return JsonResponse({'status': 'error', 'message': 'Already verified'}, status=400)

    vr.student_id_number = student_id_number
    vr.id_photo_url      = id_photo_url
    vr.selfie_url        = selfie_url
    vr.liveness_passed   = liveness_passed
    vr.status            = 'docs_submitted'
    vr.docs_submitted_at = timezone.now()
    vr.save(update_fields=['student_id_number', 'id_photo_url', 'selfie_url',
                            'liveness_passed', 'status', 'docs_submitted_at'])
    return JsonResponse({'status': 'ok', 'message': 'Documents submitted — under review within 24 h'})


@login_required(login_url='auth:auth_view')
def followers_list(request):
    """GET /profile/api/followers/ — list of users who follow the logged-in user."""
    user = request.user
    rows = (
        Follow.objects.filter(following=user)
        .select_related('follower', 'follower__profile')
        .order_by('-created_at')
    )
    data = []
    for f in rows:
        u = f.follower
        try:
            avatar = u.profile.avatar_url or ''
        except Exception:
            avatar = ''
        from Base_app.models import user_is_verified
        data.append({
            'username': u.username,
            'name': u.get_full_name() or u.username,
            'avatar': avatar,
            'is_verified': user_is_verified(u),
        })
    return JsonResponse({'results': data})


@login_required(login_url='auth:auth_view')
def following_list(request):
    """GET /profile/api/following/ — list of users the logged-in user follows."""
    user = request.user
    rows = (
        Follow.objects.filter(follower=user)
        .select_related('following', 'following__profile')
        .order_by('-created_at')
    )
    data = []
    for f in rows:
        u = f.following
        try:
            avatar = u.profile.avatar_url or ''
        except Exception:
            avatar = ''
        from Base_app.models import user_is_verified
        data.append({
            'username': u.username,
            'name': u.get_full_name() or u.username,
            'avatar': avatar,
            'is_verified': user_is_verified(u),
        })
    return JsonResponse({'results': data})


@never_cache
def followers_list_for_user(request, username):
    """GET /profile/api/followers/<username>/ — list of users who follow the given user."""
    target = get_object_or_404(User, username=username, is_active=True)
    rows = (
        Follow.objects.filter(following=target)
        .select_related('follower', 'follower__profile')
        .order_by('-created_at')
    )
    # Pre-fetch follow state for the requesting user
    current_user = request.user
    if current_user.is_authenticated:
        followed_usernames = set(
            Follow.objects.filter(follower=current_user)
            .values_list('following__username', flat=True)
        )
    else:
        followed_usernames = set()

    # Pre-fetch who follows the current user (for "Follows you" badge)
    if current_user.is_authenticated:
        followers_of_current = set(
            Follow.objects.filter(following=current_user)
            .values_list('follower__username', flat=True)
        )
    else:
        followers_of_current = set()

    data = []
    for f in rows:
        u = f.follower
        try:
            avatar = u.profile.avatar_url or ''
        except Exception:
            avatar = ''
        from Base_app.models import user_is_verified
        is_own = current_user.is_authenticated and current_user == u
        data.append({
            'username': u.username,
            'name': u.get_full_name() or u.username,
            'avatar': avatar,
            'is_verified': user_is_verified(u),
            'is_following': u.username in followed_usernames,
            'follows_you': u.username in followers_of_current,
            'is_own': is_own,
        })
    return JsonResponse({'results': data})


@never_cache
def following_list_for_user(request, username):
    """GET /profile/api/following/<username>/ — list of users the given user follows."""
    target = get_object_or_404(User, username=username, is_active=True)
    rows = (
        Follow.objects.filter(follower=target)
        .select_related('following', 'following__profile')
        .order_by('-created_at')
    )
    current_user = request.user
    if current_user.is_authenticated:
        followed_usernames = set(
            Follow.objects.filter(follower=current_user)
            .values_list('following__username', flat=True)
        )
    else:
        followed_usernames = set()

    # Pre-fetch who follows the current user (for "Follows you" badge)
    if current_user.is_authenticated:
        followers_of_current = set(
            Follow.objects.filter(following=current_user)
            .values_list('follower__username', flat=True)
        )
    else:
        followers_of_current = set()

    data = []
    for f in rows:
        u = f.following
        try:
            avatar = u.profile.avatar_url or ''
        except Exception:
            avatar = ''
        from Base_app.models import user_is_verified
        is_own = current_user.is_authenticated and current_user == u
        data.append({
            'username': u.username,
            'name': u.get_full_name() or u.username,
            'avatar': avatar,
            'is_verified': user_is_verified(u),
            'is_following': u.username in followed_usernames,
            'follows_you': u.username in followers_of_current,
            'is_own': is_own,
        })
    return JsonResponse({'results': data})


@login_required(login_url='auth:auth_view')
@require_POST
def change_password(request):
    """POST /profile/api/change-password/ — change password for logged-in user."""
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

    current  = data.get('current_password', '')
    new_pw   = data.get('new_password', '')
    confirm  = data.get('confirm_password', '')

    if not request.user.check_password(current):
        return JsonResponse({'status': 'error', 'message': 'Current password is incorrect'}, status=400)
    if len(new_pw) < 8:
        return JsonResponse({'status': 'error', 'message': 'New password must be at least 8 characters'}, status=400)
    if new_pw != confirm:
        return JsonResponse({'status': 'error', 'message': 'Passwords do not match'}, status=400)
    if new_pw == current:
        return JsonResponse({'status': 'error', 'message': 'New password must differ from current password'}, status=400)

    request.user.set_password(new_pw)
    request.user.save()

    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)

    return JsonResponse({'status': 'success', 'message': 'Password changed successfully'})


@login_required
def twofa_setup(request):
    """Generate a new TOTP secret and return the provisioning URI + QR data URL."""
    import pyotp, qrcode, base64
    from io import BytesIO
    profile = request.user.profile
    # Generate a fresh secret (not saved yet — user must confirm with a valid code first)
    secret = pyotp.random_base32()
    request.session['pending_totp_secret'] = secret
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=request.user.email or request.user.username,
        issuer_name='PU-Connect'
    )
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return JsonResponse({'secret': secret, 'qr': 'data:image/png;base64,' + qr_b64})


@login_required
@require_POST
def twofa_enable(request):
    """Verify the setup code and permanently enable 2FA."""
    import pyotp, json as _json
    secret = request.session.get('pending_totp_secret')
    if not secret:
        return JsonResponse({'status': 'error', 'message': 'No setup session found. Start setup again.'}, status=400)
    try:
        data = _json.loads(request.body)
        code = data.get('code', '').strip().replace(' ', '')
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        return JsonResponse({'status': 'error', 'message': 'Invalid code. Please try again.'}, status=400)
    profile = request.user.profile
    profile.totp_secret = secret
    profile.totp_enabled = True
    profile.save(update_fields=['totp_secret', 'totp_enabled'])
    del request.session['pending_totp_secret']
    return JsonResponse({'status': 'success', 'message': '2FA enabled successfully.'})


@login_required
@require_POST
def twofa_disable(request):
    """Disable 2FA after confirming the current TOTP code."""
    import pyotp, json as _json
    profile = request.user.profile
    if not profile.totp_enabled:
        return JsonResponse({'status': 'error', 'message': '2FA is not enabled.'}, status=400)
    try:
        data = _json.loads(request.body)
        code = data.get('code', '').strip().replace(' ', '')
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)
    totp = pyotp.TOTP(profile.totp_secret)
    if not totp.verify(code, valid_window=1):
        return JsonResponse({'status': 'error', 'message': 'Invalid code. Please try again.'}, status=400)
    profile.totp_enabled = False
    profile.totp_secret = ''
    profile.save(update_fields=['totp_secret', 'totp_enabled'])
    return JsonResponse({'status': 'success', 'message': '2FA disabled.'})


@login_required
def twofa_status(request):
    """Returns whether 2FA is currently enabled for the logged-in user."""
    return JsonResponse({'enabled': request.user.profile.totp_enabled})


def logout_view(request):
    logout(request)
    return redirect('auth:auth_view') # Standard redirect works for logout

@login_required
@require_POST
def deactivate_account(request):
    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def delete_account(request):
    user = request.user
    user.delete()
    return JsonResponse({'status': 'success'})

