from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import never_cache, cache_control
import json
import re
import textwrap
from .models import Listing

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


@login_required(login_url='auth:auth_view')
def listing_detail(request, pk):
    """Full detail page for a single listing."""
    listing = get_object_or_404(Listing, pk=pk)

    image_url = listing.image_url or ''
    if image_url and not image_url.startswith('http'):
        image_url = request.build_absolute_uri(image_url)

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

    context = {
        'listing':          listing,
        'image_url':        image_url,
        'og_image':         og_image,
        'full_url':         full_url,
        'page_title':       f"{listing.title} — PU Connect",
        'page_description': og_description,
        'seller':           seller,
        'seller_avatar':    seller_avatar,
        'seller_phone':     seller_phone,
        'seller_whatsapp':  seller_whatsapp,
        'seller_faculty':   seller_faculty,
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
    
    Displays:
    - Saved favorite items
    - Wishlist management options
    - Item details and prices
    - Option to move items to cart or remove from wishlist
    """
    context = {
        'page_title': 'Wishlist - PU-Marketplace',
        'page_description': 'View and manage your saved favorite items.',
        # Add any additional context data needed for the wishlist page here
    }
    return render(request, 'listings/wishlist.html', context)


@login_required(login_url='auth:auth_view')
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

        if not title or price is None:
            return JsonResponse({'status': 'error', 'message': 'Title and price are required'}, status=400)

        if not image_url:
            return JsonResponse({'status': 'error', 'message': 'At least one photo is required'}, status=400)

        # Update user's profile with phone number if provided
        phone = data.get('phone')
        if phone:
            from Profile_app.models import Profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.phone = phone
            profile.save()

        # Create the database entry
        new_listing = Listing.objects.create(
            user=request.user,
            title=title,
            price=price,
            description=description,
            listing_type=listing_type.lower(),
            category=category,
            subcategory=subcategory,
            condition=condition,
            image_url=image_url,
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
        listings_data.append({
            'id': item.id,
            'title': item.title,
            'price': str(item.price),
            'img': item.image_url,
            'description': item.description,
            'listing_type': item.listing_type,
            'type': item.listing_type,
            'category': item.category,
            'subcategory': item.subcategory,
            'condition': item.condition,
            'status': item.status, # Use the actual status field
            'date': item.created_at.strftime('%d %b, %Y')
        })
    return JsonResponse({'listings': listings_data})

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
        phone = ''
        try:
            phone = item.user.profile.phone or ''
        except Exception:
            pass
        listings_data.append({
            'id': item.id,
            'title': item.title,
            'price': str(item.price),
            'img': item.image_url,
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
            'status': item.status,
            'postedAt': int(item.created_at.timestamp() * 1000),
        })
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