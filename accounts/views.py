from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import login as otp_login, match_token
from .forms import SignupForm
from documents.utils import generate_qr_code_base64
import qrcode
import io
import base64

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_lockout_key(request):
    ip = get_client_ip(request)
    return f'login_attempts_{ip}'


def is_locked_out(request):
    key = get_lockout_key(request)
    attempts = cache.get(key, 0)
    return attempts >= MAX_LOGIN_ATTEMPTS


def record_failed_attempt(request):
    key = get_lockout_key(request)
    attempts = cache.get(key, 0)
    cache.set(key, attempts + 1, LOCKOUT_DURATION_SECONDS)


def clear_attempts(request):
    key = get_lockout_key(request)
    cache.delete(key)


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('setup_2fa')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if is_locked_out(request):
        return render(request, 'accounts/login.html', {
            'form': AuthenticationForm(),
            'locked_out': True,
            'lockout_minutes': LOCKOUT_DURATION_SECONDS // 60,
        })

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            clear_attempts(request)
            user = form.get_user()
            device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
            if device:
                request.session['pre_2fa_user_id'] = user.id
                return redirect('verify_2fa')
            else:
                login(request, user)
                return redirect('dashboard')
        else:
            record_failed_attempt(request)
            attempts_left = MAX_LOGIN_ATTEMPTS - cache.get(get_lockout_key(request), 0)
            if attempts_left <= 2 and attempts_left > 0:
                form.add_error(None, f"Warning: {attempts_left} attempt(s) remaining before temporary lockout.")
    else:
        form = AuthenticationForm()

    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500'
        })

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def setup_2fa_view(request):
    device, created = TOTPDevice.objects.get_or_create(
        user=request.user,
        name='default',
        defaults={'confirmed': False}
    )

    if request.method == 'POST':
        token = request.POST.get('token')
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            return redirect('dashboard')
        else:
            error = "Invalid code. Please try again."
            return render(request, 'accounts/setup_2fa.html', {
                'qr_code_data': _generate_totp_qr(device, request.user),
                'error': error
            })

    qr_code_data = _generate_totp_qr(device, request.user)
    return render(request, 'accounts/setup_2fa.html', {'qr_code_data': qr_code_data})


def _generate_totp_qr(device, user):
    config_url = device.config_url
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(config_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def verify_2fa_view(request):
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('login')

    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        token = request.POST.get('token')
        device = match_token(user, token)
        if device:
            login(request, user)
            otp_login(request, device)
            del request.session['pre_2fa_user_id']
            return redirect('dashboard')
        else:
            return render(request, 'accounts/verify_2fa.html', {'error': 'Invalid code. Try again.'})

    return render(request, 'accounts/verify_2fa.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    return render(request, 'accounts/profile.html', {'has_2fa': bool(device)})