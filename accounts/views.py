import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from .models import EmailVerificationOTP

logger = logging.getLogger(__name__)


def is_smtp_active():
    """Returns True only if real external SMTP credentials are provided."""
    user = getattr(settings, 'EMAIL_HOST_USER', '')
    pwd = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    return bool(user and pwd and 'console' not in backend.lower())


def mask_email(email):
    if not email or '@' not in email:
        return email
    parts = email.split('@', 1)
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + '*'
    else:
        masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"


def send_otp_email(user, otp_code):
    """Attempts to deliver the OTP code via email. Returns True on success, False otherwise."""
    if not is_smtp_active():
        return False

    subject = f"{otp_code} is your MobileStore verification code"
    text_content = (
        f"Hello {user.username},\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code will expire in 10 minutes. If you did not create an account on MobileStore, please ignore this email.\n\n"
        f"Best regards,\nMobileStore Team"
    )
    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 28px 24px; border: 1px solid #e2e8f0; border-radius: 16px; background: #ffffff;">
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="display: inline-block; width: 44px; height: 44px; line-height: 44px; border-radius: 12px; background: #eff6ff; font-size: 22px;">📱</div>
            <h2 style="color: #0f172a; margin: 12px 0 4px; font-size: 22px;">Verify Your Email</h2>
            <p style="color: #64748b; font-size: 14px; margin: 0;">Welcome to MobileStore, <strong>{user.username}</strong>!</p>
        </div>
        <p style="color: #334155; font-size: 14.5px; line-height: 1.5; margin-bottom: 20px;">
            Please enter the 6-digit verification code below to verify your email address and activate your customer account:
        </p>
        <div style="text-align: center; margin: 26px 0;">
            <div style="display: inline-block; background: #f8fafc; border: 2px dashed #3b82f6; border-radius: 14px; padding: 14px 32px;">
                <span style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: monospace;">{otp_code}</span>
            </div>
        </div>
        <p style="color: #64748b; font-size: 13px; text-align: center; margin: 0 0 20px;">
            ⏱️ This code expires in <strong>10 minutes</strong>.
        </p>
        <div style="border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 20px;">
            <p style="color: #94a3b8; font-size: 12px; line-height: 1.4; margin: 0;">
                If you did not request this registration, you can safely ignore this email.
            </p>
        </div>
    </div>
    """

    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MobileStore <no-reply@mobilestore.com>')
        msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {e}")
        return False


def login_view(request):
    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # 1. Check if credentials match an unverified/inactive user
        unverified_user = None
        try:
            u = User.objects.get(username__iexact=login_input)
            if u.check_password(password) and not u.is_active:
                unverified_user = u
        except User.DoesNotExist:
            try:
                u = User.objects.get(email__iexact=login_input)
                if u.check_password(password) and not u.is_active:
                    unverified_user = u
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass

        if unverified_user:
            otp = EmailVerificationOTP.generate_otp(unverified_user)
            email_sent = send_otp_email(unverified_user, otp.otp_code)
            request.session['pending_otp_user_id'] = unverified_user.id

            if email_sent:
                request.session.pop('demo_otp', None)
                messages.warning(request, f'Account is pending verification. A new 6-digit code was sent to {mask_email(unverified_user.email)}.')
            else:
                request.session['demo_otp'] = otp.otp_code
                messages.info(request, f'SMTP is in test mode. Your verification code is: {otp.otp_code}')

            return redirect('verify_otp')

        # 2. Standard authentication
        user = authenticate(request, username=login_input, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email__iexact=login_input)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('home')
        messages.error(request, 'Invalid username/email or password.')
    return render(request, 'customer/login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        p1 = request.POST.get('password', '')
        p2 = request.POST.get('confirm_password', '')

        # 1. Username validation
        if not username:
            messages.error(request, 'Please provide a valid username.')
            return render(request, 'customer/register.html')

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'customer/register.html')

        # 2. Email format validation
        if not email:
            messages.error(request, 'An email address is required for verification.')
            return render(request, 'customer/register.html')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please provide a valid email address (e.g. user@example.com).')
            return render(request, 'customer/register.html')

        # 3. Password match & complexity validation
        if p1 != p2:
            messages.error(request, 'Passwords do not match. Please verify and re-enter.')
            return render(request, 'customer/register.html')

        try:
            validate_password(p1)
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
            return render(request, 'customer/register.html')

        # 4. Duplicate checks
        if User.objects.filter(username__iexact=username, is_active=True).exists():
            messages.error(request, 'Username already registered. Please choose another username.')
            return render(request, 'customer/register.html')

        if User.objects.filter(email__iexact=email, is_active=True).exists():
            messages.error(request, 'An active account with this email already exists. Please sign in.')
            return render(request, 'customer/register.html')

        # Check if there is an inactive/pending user with this username or email to reuse
        pending_user = User.objects.filter(username__iexact=username, is_active=False).first()
        if not pending_user:
            pending_user = User.objects.filter(email__iexact=email, is_active=False).first()

        if pending_user:
            pending_user.username = username
            pending_user.email = email
            pending_user.set_password(p1)
            pending_user.save()
            user = pending_user
        else:
            user = User.objects.create_user(username=username, email=email, password=p1)
            user.is_active = False
            user.save()

        otp = EmailVerificationOTP.generate_otp(user)
        email_sent = send_otp_email(user, otp.otp_code)

        request.session['pending_otp_user_id'] = user.id

        if email_sent:
            request.session.pop('demo_otp', None)
            messages.success(request, f'Verification code sent to {mask_email(email)}! Enter the 6-digit code below.')
        else:
            request.session['demo_otp'] = otp.otp_code
            messages.info(request, f'Test Mode: Your verification code is {otp.otp_code}.')

        return redirect('verify_otp')
    return render(request, 'customer/register.html')


def verify_otp(request):
    user_id = request.session.get('pending_otp_user_id')
    if not user_id:
        messages.info(request, 'Please register or log in to verify your account.')
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.pop('pending_otp_user_id', None)
        request.session.pop('demo_otp', None)
        return redirect('signup')

    if user.is_active:
        request.session.pop('pending_otp_user_id', None)
        request.session.pop('demo_otp', None)
        return redirect('home')

    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()
        active_otp = EmailVerificationOTP.objects.filter(user=user, is_used=False).first()

        if not active_otp:
            messages.error(request, 'No active verification code found. Please click "Resend Code" below.')
        elif active_otp.attempts >= 5:
            active_otp.is_used = True
            active_otp.save()
            messages.error(request, 'Too many failed attempts. Please click "Resend Code" below to request a fresh code.')
        elif not active_otp.is_valid():
            messages.error(request, 'Verification code has expired. Please click "Resend Code" below.')
        else:
            active_otp.attempts += 1
            if active_otp.otp_code == otp_input:
                active_otp.is_used = True
                active_otp.save()
                user.is_active = True
                user.save()

                request.session.pop('pending_otp_user_id', None)
                request.session.pop('demo_otp', None)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Account activated successfully! Welcome to MobileStore, {user.first_name or user.username}.')
                return redirect('home')
            else:
                active_otp.save()
                remaining = max(0, 5 - active_otp.attempts)
                if remaining == 0:
                    active_otp.is_used = True
                    active_otp.save()
                    messages.error(request, 'Incorrect code. Maximum attempts reached. Please click "Resend Code" below.')
                else:
                    messages.error(request, f'Incorrect code. {remaining} attempt(s) remaining.')

    demo_otp = request.session.get('demo_otp')
    # If no demo_otp in session but user has an active OTP and SMTP is not active, retrieve it
    if not demo_otp and not is_smtp_active():
        active_otp = EmailVerificationOTP.objects.filter(user=user, is_used=False).first()
        if active_otp and active_otp.is_valid():
            demo_otp = active_otp.otp_code
            request.session['demo_otp'] = demo_otp

    masked = mask_email(user.email)
    return render(request, 'customer/verify_otp.html', {
        'masked_email': masked,
        'user_obj': user,
        'demo_otp': demo_otp,
    })


def resend_otp(request):
    user_id = request.session.get('pending_otp_user_id')
    if not user_id:
        messages.info(request, 'Please register or log in to request a code.')
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('signup')

    if user.is_active:
        return redirect('home')

    otp = EmailVerificationOTP.generate_otp(user)
    email_sent = send_otp_email(user, otp.otp_code)

    if email_sent:
        request.session.pop('demo_otp', None)
        messages.success(request, f'A fresh 6-digit verification code has been sent to {mask_email(user.email)}.')
    else:
        request.session['demo_otp'] = otp.otp_code
        messages.info(request, f'Test Mode: Your fresh verification code is {otp.otp_code}.')

    return redirect('verify_otp')


@csrf_protect
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


def profile(request):
    if not request.user.is_authenticated:
        messages.info(request, 'Please sign in to view your profile.')
        return redirect('login')
    return render(request, 'customer/profile.html')
