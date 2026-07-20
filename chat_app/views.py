from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
import json
from .models import Conversation, Message, Notification, PushSubscription


@login_required(login_url='auth:auth_view')
def chat(request):
    """
    Chat/Messaging Page
    GET /chat/
    """
    context = {
        'page_title': 'Messages - PU-Marketplace',
        'page_description': 'Chat with buyers and sellers.',
    }
    return render(request, 'chat/chat.html', context)

@login_required
def get_conversations(request):
    """Returns a list of all conversations for the current user."""
    convs = (
        request.user.conversations
        .select_related('listing', 'listing__user')
        .prefetch_related(
            'participants',
            'participants__profile',
        )
        .order_by('-updated_at')
    )
    me = request.user
    data = []
    for c in convs:
        other_user = next((p for p in c.participants.all() if p.id != me.id), None)
        last_msg = c.messages.select_related('sender').last()
        avatar_url = ''
        try:
            if other_user:
                avatar_url = other_user.profile.avatar_url or ''
        except Exception:
            pass
        conv_type = 'selling' if c.listing and c.listing.user_id == me.id else 'buying'
        listing_emoji = '🛠️' if c.listing and c.listing.listing_type == 'service' else '📦'
        data.append({
            'id': c.id,
            'name': other_user.get_full_name() or other_user.username if other_user else 'System',
            'username': other_user.username if other_user else 'system',
            'avatar_url': avatar_url,
            'listing': c.listing.title if c.listing else 'General',
            'listingEmoji': listing_emoji,
            'listing_image_url': c.listing.image_url if c.listing else '',
            'listing_id': c.listing.id if c.listing else None,
            'price': f"GH₵ {c.listing.price}" if c.listing else '',
            'time': last_msg.timestamp.strftime('%I:%M %p') if last_msg else 'New',
            'badge': c.messages.filter(is_read=False).exclude(sender=me).count(),
            'type': conv_type,
            'other_user_id': other_user.id if other_user else None,
            'status': 'away',
        })
    return JsonResponse(data, safe=False)


@login_required
def get_messages(request, conv_id):
    """Returns all messages for a specific conversation."""
    try:
        conv = request.user.conversations.get(id=conv_id)
        messages = conv.messages.select_related('reply_to__sender').all()
        data = []
        for m in messages:
            msg = {
                'id': m.id,
                'from': 'out' if m.sender == request.user else 'in',
                'text': m.text,
                'image_url': m.image_url,
                'voice_url': m.voice_url,
                'voice_duration': m.voice_duration if hasattr(m, 'voice_duration') else 0,
                'meetup_spot': m.meetup_spot,
                'meetup_time': m.meetup_time if m.meetup_time else None,
                'time': m.timestamp.strftime("%I:%M %p"),
                'is_read': m.is_read,
                'reply_to': m.reply_to_id,
            }
            if m.reply_to:
                msg['reply_to_name'] = 'You' if m.reply_to.sender == request.user else m.reply_to.sender.get_full_name() or m.reply_to.sender.username
                msg['reply_to_text'] = m.reply_to.text or ''
            data.append(msg)
        return JsonResponse(data, safe=False)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

@login_required
@require_POST
def start_conversation(request):
    """Starts a new conversation regarding a listing."""
    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        
        from Listings_app.models import Listing
        listing = Listing.objects.get(id=listing_id)
        seller = listing.user
        
        # Don't let users chat with themselves
        if seller == request.user:
            return JsonResponse({'status': 'error', 'message': 'You cannot start a chat with yourself'}, status=400)
        
        # One conversation per buyer-seller pair, regardless of which listing triggered it
        conv = Conversation.objects.filter(participants=request.user).filter(participants=seller).first()

        if not conv:
            conv = Conversation.objects.create(listing=listing)
            conv.participants.add(request.user, seller)
        
        return JsonResponse({'status': 'success', 'conv_id': conv.id})
    except Listing.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def start_direct(request):
    """Start or retrieve a direct conversation with a user by username (no listing required)."""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        if not username:
            return JsonResponse({'status': 'error', 'message': 'username required'}, status=400)
        other = User.objects.get(username=username)
        if other == request.user:
            return JsonResponse({'status': 'error', 'message': 'Cannot chat with yourself'}, status=400)
        conv = (
            Conversation.objects.filter(participants=request.user)
            .filter(participants=other)
            .filter(listing__isnull=True)
            .first()
        )
        if not conv:
            conv = Conversation.objects.create()
            conv.participants.add(request.user, other)
        return JsonResponse({'status': 'success', 'conv_id': conv.id})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def search_users(request):
    """Search users by username or full name for starting a new conversation."""
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse([], safe=False)
    users = User.objects.filter(
        Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
    ).exclude(id=request.user.id).select_related('profile')[:10]
    data = []
    for u in users:
        avatar_url = ''
        try:
            avatar_url = u.profile.avatar_url or ''
        except Exception:
            pass
        existing_conv = (
            Conversation.objects.filter(participants=request.user)
            .filter(participants=u)
            .first()
        )
        from Base_app.models import user_is_verified
        data.append({
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'username': u.username,
            'avatar_url': avatar_url,
            'conv_id': existing_conv.id if existing_conv else None,
            'is_verified': user_is_verified(u),
        })
    return JsonResponse(data, safe=False)

@login_required
def get_notifications(request):
    """Return the 20 most recent notifications for the current user."""
    notifs = Notification.objects.filter(user=request.user)[:20]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    data = []
    for n in notifs:
        data.append({
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'content': n.content,
            'link': n.link or '',
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d %b, %I:%M %p'),
        })
    return JsonResponse({'notifications': data, 'unread_count': unread_count})


@login_required
@require_POST
def mark_notifications_read(request):
    """Mark all (or one) notifications as read."""
    try:
        data = json.loads(request.body) if request.body else {}
        notif_id = data.get('id')
        if notif_id:
            Notification.objects.filter(user=request.user, id=notif_id).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def push_subscribe(request):
    """Save or update a Web Push subscription for the current user/device."""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint', '').strip()
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh', '').strip()
        auth = keys.get('auth', '').strip()
        if not endpoint or not p256dh or not auth:
            return JsonResponse({'status': 'error', 'message': 'Invalid subscription'}, status=400)
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={'user': request.user, 'p256dh': p256dh, 'auth': auth},
        )
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def push_unsubscribe(request):
    """Remove a Web Push subscription (called when user unsubscribes)."""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint', '').strip()
        PushSubscription.objects.filter(endpoint=endpoint).delete()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
