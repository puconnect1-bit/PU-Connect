from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache, cache_control
from django.utils import timezone
import json
import re
import textwrap
from .models import Listing, Wishlist
from Base_app.models import user_is_verified

@cache_control(max_age=86400, public=True)
def listing_og_image(request, pk):
    """
    Returns a 1200×630 SVG branded card for use as og:image.
    Cached 24 h publicly — crawlers and CDNs can cache it.
    """
    listing = get_object_or_404(Listing, pk=pk)

    # Truncate title and description safely for SVG text
    title = listing.title or 'Listing'
    price = f"GH₵ {listing.price}" if not listing.contact_for_price else "Contact for price"
    category = listing.category or ''
    seller = listing.user.get_full_name() or listing.user.username

    # Wrap title into up to 2 lines of ~32 chars
    lines = textwrap.wrap(title, width=32)[:2]
    title_line1 = _svg_escape(lines[0]) if len(lines) > 0 else ''
    title_line2 = _svg_escape(lines[1]) if len(lines) > 1 else ''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0F1117"/>
      <stop offset="100%" stop-color="#1A1D27"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#e8c96a"/>
      <stop offset="100%" stop-color="#c9a030"/>
    </linearGradient>
    <clipPath id="img-clip">
      <rect x="720" y="0" width="480" height="630" rx="0"/>
    </clipPath>
  </defs>

  <!-- Background -->
  <rect width="1200" height="630" fill="url(#bg)"/>

  <!-- Left accent bar -->
  <rect x="0" y="0" width="6" height="630" fill="url(#accent)"/>

  <!-- Right image panel background -->
  <rect x="720" y="0" width="480" height="630" fill="#22263A"/>

  <!-- Decorative circle -->
  <circle cx="960" cy="315" r="220" fill="none" stroke="#e8c96a" stroke-width="1.5" opacity="0.12"/>
  <circle cx="960" cy="315" r="160" fill="none" stroke="#e8c96a" stroke-width="1" opacity="0.08"/>

  <!-- PU Connect branding (top-left) -->
  <text x="60" y="72" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#e8c96a">PU</text>
  <text x="105" y="72" font-family="Arial, sans-serif" font-size="28" font-weight="400" fill="#ffffff">Connect</text>

  <!-- Divider under brand -->
  <rect x="60" y="88" width="120" height="2" fill="url(#accent)" rx="1"/>

  <!-- Category badge -->
  <rect x="60" y="120" width="{min(len(category) * 13 + 32, 300)}" height="34" rx="17" fill="#22263A"/>
  <text x="76" y="143" font-family="Arial, sans-serif" font-size="16" fill="#e8c96a" font-weight="600">{_svg_escape(category)}</text>

  <!-- Listing title line 1 -->
  <text x="60" y="230" font-family="Arial, sans-serif" font-size="52" font-weight="700" fill="#ffffff">{title_line1}</text>
  {"" if not title_line2 else f'<text x="60" y="295" font-family="Arial, sans-serif" font-size="52" font-weight="700" fill="#ffffff">{title_line2}</text>'}

  <!-- Price -->
  <text x="60" y="{340 if title_line2 else 310}" font-family="Arial, sans-serif" font-size="42" font-weight="800" fill="#e8c96a">{_svg_escape(price)}</text>

  <!-- Seller -->
  <text x="60" y="{420 if title_line2 else 390}" font-family="Arial, sans-serif" font-size="20" fill="#9ca3af">Listed by <tspan fill="#d1d5db" font-weight="600">{_svg_escape(seller)}</tspan></text>

  <!-- CTA bar at bottom -->
  <rect x="0" y="560" width="720" height="70" fill="#1A1D27"/>
  <text x="60" y="602" font-family="Arial, sans-serif" font-size="20" fill="#6b7280">pentvarsconnect.com</text>
  <rect x="540" y="573" width="140" height="44" rx="22" fill="url(#accent)"/>
  <text x="610" y="601" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#0F1117" text-anchor="middle">View Listing</text>

  <!-- Right panel placeholder icon when no image -->
  <text x="960" y="290" font-family="Arial, sans-serif" font-size="90" text-anchor="middle" fill="#e8c96a" opacity="0.25">🛒</text>
  <text x="960" y="370" font-family="Arial, sans-serif" font-size="22" text-anchor="middle" fill="#6b7280">Campus Marketplace</text>
</svg>'''

    return HttpResponse(svg, content_type='image/svg+xml')


def _svg_escape(text):
    """Escape special XML characters for safe SVG embedding."""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def split_listing_images(value):
    """Normalize a single or multi-image payload into a stable ordered URL list."""
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        urls = []
        for item in value:
            urls.extend(split_listing_images(item))
        return [url for url in dict.fromkeys(urls) if url]

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []

        try:
            decoded = json.loads(text)
        except Exception:
            decoded = None

        if isinstance(decoded, dict):
            for key in ('images', 'image_urls', 'image_url'):
                if key in decoded:
                    return split_listing_images(decoded[key])

        if isinstance(decoded, (list, tuple)):
            return split_listing_images(list(decoded))

        parts = re.split(r'[\n,;]+', text)
        urls = []
        for part in parts:
            part = part.strip().strip('[]\'"')
            if part:
                urls.append(part)
        return [url for url in dict.fromkeys(urls) if url]

        return [str(value)]


def serialize_listing(item):
    """Serialize a Listing into the canonical dict shape consumed by the card
    renderers (search feed, dashboard, detail page, and wishlist).

    Centralised here so the Wishlist API and the listing feed stay in lockstep.
    Decimal price / timestamps are coerced to JSON-friendly types.
    """
    phone = ''
    try:
        phone = item.user.profile.phone or ''
    except Exception:
        pass
    image_urls = split_listing_images(item.image_url)
    primary_image_url = image_urls[0] if image_urls else ''
    return {
        'id': item.id,
        'title': item.title,
        'price': str(item.price),
        'img': primary_image_url,
        'images': image_urls,
        'description': item.description,
        'listing_type': item.listing_type,
        'type': item.listing_type,
        'category': item.category,
        'subcategory': item.subcategory,
        'condition': item.condition,
        'seller': item.user.get_full_name() or item.user.username,
        'sellerUsername': item.user.username,
        'phone': phone,
        'contact_for_price': item.contact_for_price,
        'priceLabel': 'Contact for Price' if item.contact_for_price else '',
        'negotiable': False,
        'status': item.status,
        'postedAt': int(item.created_at.timestamp() * 1000),
    }


def listing_detail(request, pk):
    """Full detail page for a single listing."""
    listing = get_object_or_404(Listing, pk=pk)

    image_urls = split_listing_images(listing.image_url)
    image_urls = [
        url if url.startswith(('http://', 'https://')) else request.build_absolute_uri(url)
        for url in image_urls
    ]
    image_url = image_urls[0] if image_urls else ''

    seller = listing.user
    try:
        seller_profile = seller.profile
        seller_avatar  = seller_profile.avatar_url or ''
        seller_phone   = seller_profile.phone or ''
        seller_faculty = seller_profile.faculty or ''
    except Exception:
        seller_avatar  = ''
        seller_phone   = ''
        seller_faculty = ''

    # Format phone for WhatsApp: digits only, leading 0 → Ghana code 233
    _digits = re.sub(r'\D', '', seller_phone)
    if _digits.startswith('0'):
        _digits = '233' + _digits[1:]
    elif _digits and not _digits.startswith('233'):
        _digits = '233' + _digits
    seller_whatsapp = _digits  # empty string if no phone

    full_url = request.build_absolute_uri()
    # Use the real R2 image if present, otherwise fall back to the branded SVG card
    og_image = image_url if image_url else request.build_absolute_uri(f'/listings/{pk}/og-image/')

    price_display = f"GH₵ {listing.price}" if not listing.contact_for_price else "Contact for price"
    og_description = (
        f"{price_display} · {listing.category} · {listing.description[:120]}"
        if listing.description
        else f"{price_display} · {listing.category} · Listed on PU Connect"
    )

    from Base_app.models import user_is_verified
    context = {
        'listing':          listing,
        'image_url':        image_url,
        'image_urls':       image_urls,
        'og_image':         og_image,
        'full_url':         full_url,
        'page_title':       f"{listing.title} — PU Connect",
        'page_description': og_description,
        'seller':           seller,
        'seller_avatar':    seller_avatar,
        'seller_phone':     seller_phone,
        'seller_whatsapp':  seller_whatsapp,
        'seller_faculty':   seller_faculty,
        'seller_verified':  user_is_verified(seller),
        'is_owner':         request.user.is_authenticated and request.user == seller,
    }
    return render(request, 'listings/detail.html', context)

@login_required(login_url='auth:auth_view')

def listings(request):
    """
    My Listings Page
    GET /listings/
    
    Displays:
    - User's active listings
    - Listing management options
    - Create new listing button
    - Listing performance metrics
    """
    context = {
        'page_title': 'My Listings - PU-Marketplace',
        'page_description': 'Manage your product and service listings.',
        # Add any additional context data needed for the listings page here
    }
    return render(request, 'listings/listings.html', context)


@login_required(login_url='auth:auth_view')
def wishlist(request):
    """
    Wishlist Page
    GET /listings/wishlist/

    Server-driven: saved items for the current user are read from the Wishlist
    model and passed straight to the template. The page JS also fetches the
    /listings/api/wishlist/ endpoint on load so the grid always matches the
    database, and removing an item calls /listings/api/wishlist/toggle/.
    """
    saved = list(
        Wishlist.objects.filter(user=request.user)
        .select_related('listing', 'listing__user', 'listing__user__profile')
        .order_by('-created_at')
    )
    saved_items = [serialize_listing(w.listing) for w in saved]
    context = {
        'page_title': 'Wishlist - PU-Marketplace',
        'page_description': 'View and manage your saved favorite items.',
        'saved_items': saved_items,
    }
    return render(request, 'listings/wishlist.html', context)


@login_required(login_url='auth:auth_view')
@require_POST
def toggle_wishlist_api(request):
    """
    POST /listings/api/wishlist/toggle/

    Accepts {"listing_id": <id>} in JSON or form-encoded body and toggles the
    current user's saved state for that listing. Responds with the new state so
    the client can update the UI.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required'}, status=401)
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = json.loads(request.body or b'{}')
        else:
            data = request.POST.dict()
    except Exception:
        data = {}

    try:
        listing_id = int(data.get('listing_id'))
    except (TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'listing_id is required'}, status=400)

    if not Listing.objects.filter(id=listing_id).exists():
        return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)

    # Race-safe toggle: get_or_create then delete if it already existed.
    obj, created = Wishlist.objects.get_or_create(user=request.user, listing_id=listing_id)
    if not created:
        obj.delete()
        saved = False
    else:
        saved = True

    return JsonResponse({'status': 'success', 'saved': saved, 'listing_id': listing_id})


@login_required(login_url='auth:auth_view')
def wishlist_data_api(request):
    """
    GET /listings/api/wishlist/

    Returns the current user's saved listings as JSON, using the same canonical
    shape (serialize_listing) the card renderers consume.
    """
    saved = list(
        Wishlist.objects.filter(user=request.user)
        .select_related('listing', 'listing__user', 'listing__user__profile')
        .order_by('-created_at')
    )
    saved_items = [serialize_listing(w.listing) for w in saved]
    return JsonResponse({'listings': saved_items})


@login_required(login_url='auth:auth_view')
def create_listing(request):
    """
    Create Listing Page
    GET /listings/create/

    Displays:
    - Listing creation form
    - Product/service details form
    - Photo upload
    - Pricing form
    """
    context = {
        'page_title': 'Create New Listing - PU-Marketplace',
        'page_description': 'Post a new item or service.',
    }
    return render(request, 'listings/create-listing.html', context)




@login_required(login_url='auth:auth_view')
@require_POST
def create_listing_api(request):
    """
    Saves listing data and the R2 image URL to the database.
    """
    try:
        data = json.loads(request.body)

        title = data.get('title')
        price = data.get('price')
        description = data.get('description', '')
        listing_type = data.get('listing_type', 'product')
        category = data.get('category', '')
        subcategory = data.get('subcategory', '')
        condition = data.get('condition', '')
        image_url = data.get('image_url', '')
        contact_for_price = data.get('contact_for_price', False)

        image_urls = split_listing_images(image_url)
        if not image_urls:
            return JsonResponse({'status': 'error', 'message': 'At least one photo is required'}, status=400)

        if not title or price is None:
            return JsonResponse({'status': 'error', 'message': 'Title and price are required'}, status=400)

        from Base_app.models import SiteConfig
        _cfg = SiteConfig.get()
        active_count = Listing.objects.filter(user=request.user, status__in=['active', 'boosted', 'paused']).count()
        if active_count >= _cfg.max_listings_per_user:
            return JsonResponse({'status': 'error', 'message': f'Listing limit reached ({_cfg.max_listings_per_user} max)'}, status=400)

        # Update user's profile with phone number if provided
        phone = data.get('phone')
        if phone:
            from Profile_app.models import Profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.phone = phone
            profile.save()

        # Create the database entry
        stored_image_url = ', '.join(image_urls)

        new_listing = Listing.objects.create(
            user=request.user,
            title=title,
            price=price,
            description=description,
            listing_type=listing_type.lower(),
            category=category,
            subcategory=subcategory,
            condition=condition,
            image_url=stored_image_url,
            contact_for_price=contact_for_price,
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Listing created successfully!',
            'listing_id': new_listing.id
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

@login_required
def get_my_listings(request):
    """
    Fetches listings for the logged-in user to display in the UI.
    """
    listings = Listing.objects.filter(user=request.user).order_by('-created_at')
    listings_data = []
    for item in listings:
        image_urls = split_listing_images(item.image_url)
        primary_image_url = image_urls[0] if image_urls else ''
        listings_data.append({
            'id': item.id,
            'title': item.title,
            'price': str(item.price),
            'contact_for_price': item.contact_for_price,
            'img': primary_image_url,
            'images': image_urls,
            'description': item.description,
            'listing_type': item.listing_type,
            'type': item.listing_type,
            'category': item.category,
            'subcategory': item.subcategory,
            'condition': item.condition,
            'status': item.status,
            'views': 0,
            'date': item.created_at.strftime('%d %b, %Y')
        })
    return JsonResponse({'listings': listings_data})

@never_cache
def latest_listings_partials(request):
    """
    HTMX partial — returns only listings with an id greater than the newest
    listing the client already holds (passed as ?last_id=). Combined with
    hx-swap="afterbegin", brand-new cards are prepended to the top of the feed
    without a page refresh.

    The client tracks the highest listing id it has rendered (window.__puLastId)
    and sends it on every poll, so this endpoint only ever returns genuinely new
    rows. When nothing is newer it responds 204 No Content and HTMX leaves the
    DOM untouched — no empty markup, no repeated cards.
    """
    from django.db.models import Case, When, IntegerField

    try:
        last_id = int(request.GET.get('last_id', 0))
    except (TypeError, ValueError):
        last_id = 0

    items = list(
        Listing.objects
        .filter(status__in=['active', 'boosted'], id__gt=last_id)
        .select_related('user', 'user__profile')
        .order_by(
            Case(When(status='boosted', then=0), default=1, output_field=IntegerField()),
            '-created_at',
        )[:40]
    )

    # Nothing newer than the client's cutoff -> 204 so HTMX swaps in nothing.
    if not items:
        return HttpResponse(status=204)

    cards = []
    for item in items:
        phone = ''
        try:
            phone = item.user.profile.phone or ''
        except Exception:
            pass
        image_urls = split_listing_images(item.image_url)
        primary_image_url = image_urls[0] if image_urls else ''
        try:
            seller_verified = user_is_verified(item.user)
        except Exception:
            seller_verified = False
        cards.append({
            'id': item.id,
            'title': item.title,
            'price': str(item.price),
            'contact_for_price': item.contact_for_price,
            'img': primary_image_url,
            'listing_type': item.listing_type,
            'type': item.listing_type,
            'category': item.category,
            'seller': item.user.get_full_name() or item.user.username,
            'seller_verified': seller_verified,
            'postedAt': int(item.created_at.timestamp() * 1000),
        })

    return render(request, 'listings/_latest_card.html', {'listings': cards})


@never_cache
def get_all_listings(request):
    """
    Fetches available listings for the dashboard with pagination.
    ?page=1&page_size=60
    """
    from django.db.models import Case, When, IntegerField

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    page_size = 60
    offset = (page - 1) * page_size

    qs = (
        Listing.objects
        .filter(status__in=['active', 'boosted'])
        .select_related('user', 'user__profile')
        .order_by(
            Case(When(status='boosted', then=0), default=1, output_field=IntegerField()),
            '-created_at',
        )
    )
    total = qs.count()
    listings = qs[offset:offset + page_size]

    listings_data = []
    for item in listings:
        listings_data.append(serialize_listing(item))
    return JsonResponse({
        'listings': listings_data,
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_next': offset + page_size < total,
    })

@login_required
@require_POST
def delete_listing_api(request, listing_id):
    """Deletes a listing owned by the user."""
    try:
        listing = Listing.objects.get(id=listing_id, user=request.user)
        listing.delete()
        return JsonResponse({'status': 'success', 'message': 'Listing deleted'})
    except Listing.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)

@login_required
@require_POST
def toggle_listing_status_api(request, listing_id):
    """Toggles status between active and paused, or marks as sold."""
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        listing = Listing.objects.get(id=listing_id, user=request.user)
        
        if new_status in ['active', 'paused', 'sold', 'boosted']:
            listing.status = new_status
            # Sync is_available for backward compatibility
            listing.is_available = (new_status in ['active', 'boosted'])
            listing.save()
            return JsonResponse({'status': 'success', 'new_status': listing.status})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)
    except Listing.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='auth:auth_view')
@require_POST
def report_listing(request, pk):
    """POST /listings/<pk>/report/ — report a listing."""
    listing = get_object_or_404(Listing, pk=pk)
    if listing.user == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot report your own listing'}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    reason = data.get('reason', '').strip()
    details = data.get('details', '').strip()
    valid_reasons = {'spam', 'scam', 'fake', 'prohibited', 'harassment', 'inappropriate', 'off_platform', 'other'}
    if reason not in valid_reasons:
        return JsonResponse({'status': 'error', 'message': 'Invalid reason'}, status=400)
    from .models import ListingReport
    if ListingReport.objects.filter(listing=listing, reporter=request.user, status='open').exists():
        return JsonResponse({'status': 'error', 'message': 'You already have an open report for this listing'}, status=400)
    report = ListingReport.objects.create(
        listing=listing,
        reporter=request.user,
        reason=reason,
        details=details,
    )
    # Notify admins
    from .signals import send_listing_report_notifications
    send_listing_report_notifications(report)
    return JsonResponse({'status': 'success', 'message': 'Report submitted. Our team will review it shortly.'})
