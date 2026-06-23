import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.shortcuts import render

from django.contrib.auth.models import User

from django.db import IntegrityError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse

# API endpoint for user login

@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'status': 'error', 'message': 'Username and password are required.'}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = user.profile
                if profile.totp_enabled and profile.totp_secret:
                    # Park the user ID in session; do NOT call login() yet
                    request.session['pending_2fa_user_id'] = user.pk
                    request.session['pending_2fa_backend'] = 'django.contrib.auth.backends.ModelBackend'
                    return JsonResponse({'status': 'require_2fa'}, status=200)
            except Exception:
                pass
            login(request, user)
            return JsonResponse({'status': 'success', 'message': 'Login successful'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid email or password.'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'A server error occurred.'}, status=500)


@require_POST
def verify_2fa_view(request):
    """Completes login for users who have 2FA enabled."""
    pending_id = request.session.get('pending_2fa_user_id')
    if not pending_id:
        return JsonResponse({'status': 'error', 'message': 'No pending 2FA session.'}, status=400)

    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().replace(' ', '')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)

    if not code:
        return JsonResponse({'status': 'error', 'message': 'Code is required.'}, status=400)

    try:
        import pyotp
        from django.contrib.auth.models import User as _User
        user = _User.objects.get(pk=pending_id)
        totp = pyotp.TOTP(user.profile.totp_secret)
        if not totp.verify(code, valid_window=1):
            return JsonResponse({'status': 'error', 'message': 'Invalid or expired code.'}, status=401)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Verification failed.'}, status=500)

    # Clear the pending flag and complete login
    del request.session['pending_2fa_user_id']
    request.session.pop('pending_2fa_backend', None)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    return JsonResponse({'status': 'success', 'message': 'Login successful'}, status=200)
    

#===================================================





def signup_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            fname = data.get('fname', '').strip()
            lname = data.get('lname', '').strip()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')

            # Server-side validation
            if not all([fname, lname, username, email, password]):
                return JsonResponse({'success': False, 'message': 'All fields are required.'}, status=400)

            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'success': False, 'message': 'Invalid email format.'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists.'}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email already registered.'}, status=400)

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=fname,
                last_name=lname
            )
            
            # Log the user in after registration
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return JsonResponse({
                'success': True, 
                'message': 'Account created successfully!', 
                'redirect': reverse('dashboard:dashboard')
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)
#===================================================




@ensure_csrf_cookie
def login_page(request):
    return render(request, 'login.html')


@ensure_csrf_cookie
def two_fa_page(request):
    """Renders the 2FA code-entry page. Rejects users with no pending session."""
    if not request.session.get('pending_2fa_user_id'):
        from django.shortcuts import redirect
        return redirect('auth:auth_view')
    return render(request, 'auth/two_fa.html')


# Additional views for registration, password reset, etc. can be added here as needed.

@ensure_csrf_cookie
def Auth_view(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard:dashboard')
    context = {
        'page_title': 'Login/Sign Up - PU Connect',
        'page_description': 'Join the PU Connect community.',
    }
    return render(request, 'auth/auth.html', context)