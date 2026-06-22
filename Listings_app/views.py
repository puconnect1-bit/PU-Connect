from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
import json
import re
from .models import Listing

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

    context = {
        'listing':        listing,
        'image_url':      image_url,
        'full_url':       request.build_absolute_uri(),
        'page_title':     f"{listing.title} — PU-Connect",
        'page_description': listing.description[:160] if listing.description else "Check out this listing on PU-Connect.",
        'seller':         seller,
        'seller_avatar':  seller_avatar,
        'seller_phone':   seller_phone,
        'seller_whatsapp': seller_whatsapp,
        'seller_faculty': seller_faculty,
        'is_owner':       request.user.is_authenticated and request.user == seller,
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
    Fetches all available listings to display on the dashboard.
    """
    # Boosted listings first, then active by most recent
    from django.db.models import Case, When, IntegerField
    listings = Listing.objects.filter(status__in=['active', 'boosted']).order_by(
        Case(When(status='boosted', then=0), default=1, output_field=IntegerField()),
        '-created_at',
    )
    listings_data = []
    for item in listings:
        phone = ""
        try:
            if hasattr(item.user, 'profile') and item.user.profile.phone:
                phone = item.user.profile.phone
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
            'postedAt': int(item.created_at.timestamp() * 1000)
        })
    return JsonResponse(listings_data, safe=False)

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