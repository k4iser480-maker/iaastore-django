from django.shortcuts import render, redirect
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Account
from .forms import RegistrationForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests

@never_cache
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.save()

#user activation
            current_site = get_current_site(request)
            mail_subject = 'Por favor activa tu cuenta'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()
            return redirect('/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@never_cache
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            account = Account.objects.get(email=email)
        except Account.DoesNotExist:
            messages.error(request, 'No existe una cuenta con ese correo.')
            return redirect('login')

        if not account.is_active:
            messages.error(request, 'unverified:' + email)
            return redirect('login')

        user = auth.authenticate(email=email, password=password)
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_items_exists = CartItem.objects.filter(cart=cart)
                if is_cart_items_exists.exists():
                    cart_items = CartItem.objects.filter(cart=cart)
                    for item in cart_items:
                        existing = CartItem.objects.filter(user=user, product=item.product).first()
                        if existing:
                            existing.quantity += item.quantity
                            existing.save()
                            item.delete()
                        else:
                            item.user = user
                            item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'Has iniciado sesion.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                print('query ->', query)
                print('----')
                #next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Contraseña incorrecta. Por favor intentalo de nuevo.')
            return redirect('login')

    return render(request, 'accounts/login.html')


def logout(request):
    auth.logout(request)
    messages.success(request, 'Has cerrado sesion.')
    return redirect('login')


def resend_verification(request):
    email = request.GET.get('email')
    if email:
        try:
            user = Account.objects.get(email=email)
            if not user.is_active:
                current_site = get_current_site(request)
                mail_subject = 'Por favor activa tu cuenta'
                message = render_to_string('accounts/account_verification_email.html', {
                    'user': user,
                    'domain': current_site,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                send_email = EmailMessage(mail_subject, message, to=[email])
                send_email.send()
        except Account.DoesNotExist:
            pass
    return redirect('/accounts/login/?command=verification&email=' + (email or ''))


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Tu cuenta ha sido activada. Ya puedes iniciar sesion.')
        return redirect('login')
    else:
        messages.error(request, 'El enlace de activacion es invalido.')
        return redirect('register')

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user: Account = Account.objects.get(email__exact=email)
            
            #reset password email
            current_site = get_current_site(request)
            mail_subject = 'Restablece tu contraseña'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Te hemos enviado un correo para restablecer tu contraseña.')
            return redirect('login')
        else:
            messages.error(request, 'No existe una cuenta con ese correo.')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        return redirect('resetPassword')
    else:
        messages.error(request, 'El enlace de restablecimiento ha expirado o es invalido.')
        return redirect('forgotPassword')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Tu contraseña ha sido restablecida. Ya puedes iniciar sesion.')
            return redirect('login')
        else:
            messages.error(request, 'Las contraseñas no coinciden. Por favor intentalo de nuevo.')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')