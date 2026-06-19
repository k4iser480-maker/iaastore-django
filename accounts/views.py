from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Account, ShippingAddress, ReferralProfile, Referral
from .forms import RegistrationForm, ShippingAddressForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests
import random
import string

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
            
            # Create ReferralProfile
            base_ref_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            ReferralProfile.objects.create(user=user, referral_code=base_ref_code)

            # Process Referral if referred
            ref_code = request.session.get('ref_code')
            if ref_code:
                try:
                    referrer_profile = ReferralProfile.objects.get(referral_code=ref_code)
                    Referral.objects.create(
                        referrer=referrer_profile.user,
                        referred=user
                    )
                except ReferralProfile.DoesNotExist:
                    pass
                # Clear from session
                del request.session['ref_code']

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
    # If user is already authenticated, redirect immediately
    if request.user.is_authenticated:
        if request.user.is_transportista:
            return redirect('transportista:transportista_dashboard')
        return redirect('dashboard')

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

            # Transportistas: redirect directly to their dashboard, ignore ?next
            if user.is_transportista:
                messages.success(request, 'Has iniciado sesión.')
                return redirect('transportista:transportista_dashboard')

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
    from orders.models import Order, OrderProduct
    from store.models import ReviewRating, Wishlist

    orders = Order.objects.filter(user=request.user).exclude(payment_status='pending').order_by('-created_at')
    reviews = ReviewRating.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product').order_by('-created_at')

    total_orders = orders.count()
    completed_orders = orders.filter(status='Completed').count()
    pending_orders = orders.filter(status__in=['New', 'Processing']).count()
    total_reviews = reviews.count()
    
    shipping_addresses = ShippingAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    context = {
        'orders': orders,
        'reviews': reviews,
        'wishlist_items': wishlist_items,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'total_reviews': total_reviews,
        'shipping_addresses': shipping_addresses,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.save()
        messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
        return redirect('dashboard')
    return redirect('dashboard')


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return redirect('dashboard')

        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas nuevas no coinciden.')
            return redirect('dashboard')

        if len(new_password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return redirect('dashboard')

        user.set_password(new_password)
        user.save()
        auth.update_session_auth_hash(request, user)
        messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
        return redirect('dashboard')
    return redirect('dashboard')


@login_required(login_url='login')
def order_detail(request, order_number):
    from orders.models import Order, OrderProduct
    from orders.services.delivery_service import DeliveryService

    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
        if order.payment_status == 'pending':
            raise Order.DoesNotExist
    except Order.DoesNotExist:
        messages.error(request, 'Pedido no encontrado.')
        return redirect('dashboard')

    order_products = OrderProduct.objects.filter(order=order)

    # Compute sub_total for each item
    for item in order_products:
        item.sub_total = item.quantity * item.product_price

    subtotal = sum(item.sub_total for item in order_products)
    
    # Delivery Tracking
    checkpoints = None
    tracking_step = 0
    city_lat = None
    city_lng = None
    
    if order.is_delivery:
        checkpoints = order.checkpoints.all()
        tracking_step = DeliveryService.get_tracking_step(order)
        city_coords = DeliveryService.get_city_coordinates(order.city)
        city_lat = city_coords['lat']
        city_lng = city_coords['lng']

    context = {
        'order': order,
        'order_products': order_products,
        'subtotal': subtotal,
        'checkpoints': checkpoints,
        'tracking_step': tracking_step,
        'city_lat': city_lat,
        'city_lng': city_lng,
    }
    return render(request, 'accounts/order_detail.html', context)
@login_required(login_url='login')
def confirm_delivery(request, order_number):
    from orders.models import Order
    if request.method == 'POST':
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
            if order.payment_status == 'pending':
                raise Order.DoesNotExist
            if order.status == 'Delivered':
                order.status = 'Completed'
                order.save()
                messages.success(request, '¡Has confirmado la recepción de tu pedido! Gracias por tu compra.')
            else:
                messages.error(request, 'El pedido no se encuentra en estado entregado.')
        except Order.DoesNotExist:
            messages.error(request, 'Pedido no encontrado.')
            
    return redirect('dashboard')

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

@login_required(login_url='login')
def shipping_addresses(request):
    addresses = ShippingAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'accounts/dashboard.html', {'shipping_addresses': addresses, 'active_tab': 'addresses'})

@login_required(login_url='login')
def add_shipping_address(request):
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # Si es la primera dirección, establecerla como predeterminada
            if ShippingAddress.objects.filter(user=request.user).count() == 0:
                address.is_default = True
            address.save()
            messages.success(request, 'Dirección agregada correctamente.')
            return redirect('dashboard')
    else:
        form = ShippingAddressForm()
    return render(request, 'accounts/shipping_address_form.html', {'form': form, 'action': 'Crear'})

@login_required(login_url='login')
def edit_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dirección actualizada correctamente.')
            return redirect('dashboard')
    else:
        form = ShippingAddressForm(instance=address)
    return render(request, 'accounts/shipping_address_form.html', {'form': form, 'action': 'Editar'})

@login_required(login_url='login')
def delete_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Dirección eliminada correctamente.')
    return redirect('dashboard')

@login_required(login_url='login')
def set_default_shipping_address(request, address_id):
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    ShippingAddress.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, 'Dirección predeterminada actualizada.')
    return redirect('dashboard')