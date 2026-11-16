import json
from urllib.parse import urlsplit

import jwt
from jwt import PyJWKClient

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST


def login_view(request):
    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=login_input, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email__iexact=login_input)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username/email or password.')
    return render(request, 'customer/login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        p1 = request.POST.get('password', '')
        p2 = request.POST.get('confirm_password', '')
        if p1 != p2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username already exists. Please choose another.')
        else:
            User.objects.create_user(username=username, email=email, password=p1)
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    return render(request, 'customer/register.html')


from django.views.decorators.csrf import csrf_protect


@csrf_protect
def logout_view(request):
    logout(request)
    return redirect('home')


def profile(request): return render(request,'customer/profile.html')



@require_POST
def neon_session(request):
    try:
        body = json.loads(request.body)
        token = body.get("token")

        if not isinstance(token, str) or not token:
            return JsonResponse(
                {"error": "Authentication token is required."},
                status=400
            )

        auth_url = urlsplit(settings.NEON_AUTH_BASE_URL)
        issuer = f"{auth_url.scheme}://{auth_url.netloc}"

        jwks_client = PyJWKClient(
            settings.NEON_AUTH_JWKS_URL,
            cache_keys=True
        )

        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            issuer=issuer,
            audience=issuer,
            options={
                "require": ["exp", "iat", "sub", "iss", "aud"]
            }
        )

        neon_user_id = payload.get("sub")

        if not isinstance(neon_user_id, str) or not neon_user_id:
            return JsonResponse(
                {"error": "Invalid user identity."},
                status=401
            )

        username = f"neon_{neon_user_id}"

        if len(username) > 150:
            return JsonResponse(
                {"error": "Invalid user identity."},
                status=401
            )

        email = ""
        if payload.get("email_verified") is True:
            claim_email = payload.get("email")
            if isinstance(claim_email, str):
                email = claim_email[:254]

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email}
            )

            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            elif email and user.email != email:
                user.email = email
                user.save(update_fields=["email"])

            if not user.is_active:
                return JsonResponse(
                    {"error": "This account is inactive."},
                    status=403
                )

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend"
        )

        return JsonResponse({"success": True})

    except (jwt.InvalidTokenError, jwt.PyJWKClientError):
        return JsonResponse(
            {"error": "Invalid or expired authentication token."},
            status=401
        )

    except (ValueError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Invalid request."},
            status=400
        )

    except Exception:
        return JsonResponse(
            {"error": "Authentication service is temporarily unavailable."},
            status=503
        )
