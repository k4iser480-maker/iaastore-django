from django.shortcuts import render
from store.models import Product
from .models import Cart, CartItem
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from store.shipping_utils import calculate_shipping
from orders.services.discount_service import DiscountService

# Create your views here.
def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart

def add_cart(request, product_id):
    product=Product.objects.get(id=product_id)#obtener el producto
    try:
        cart=Cart.objects.get(cart_id=_cart_id(request))#obtener el carrito usando el id de la sesión
    except Cart.DoesNotExist:
        cart=Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
    
    qty = 1
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
        except ValueError:
            qty = 1

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += qty
        cart_item.save()
    except CartItem.DoesNotExist:
        # create a new item and save it
        cart_item = CartItem.objects.create(product=product, cart=cart, quantity=qty, user=request.user if request.user.is_authenticated else None)
        cart_item.save()
    return redirect('cart')


def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.filter(product=product, user=request.user).first()
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.filter(product=product, cart=cart).first()
    except CartItem.DoesNotExist:
        return redirect('cart')
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

def remove_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        CartItem.objects.filter(product=product, user=request.user).delete()
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            CartItem.objects.filter(product=product, cart=cart).delete()
        except Cart.DoesNotExist:
            pass
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        total_weight = 0
        shipping_cost = 0
        discount_amount = 0
        coupon_code = request.session.get('coupon_code', None)
        coupon_msg = None
        
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
            
        for cart_item in cart_items:
            total+=(cart_item.product.price * cart_item.quantity)
            quantity+=cart_item.quantity
        
        # Calculate shipping
        total_weight, shipping_cost = calculate_shipping(cart_items, total)

        # Apply discount
        if coupon_code:
            is_valid, discount_amount, coupon_obj, coupon_msg = DiscountService.apply_coupon(
                request.user if request.user.is_authenticated else None,
                total,
                coupon_code
            )
            if not is_valid:
                # Remove invalid coupon
                request.session['coupon_code'] = None
                discount_amount = 0
                messages.warning(request, f"Cupón removido: {coupon_msg}")
            
        discounted_total = total - discount_amount

        # IVA 16% for VES, IGTF 3% for USD
        currency = request.session.get('currency', 'USD')
        if currency == 'VES':
            tax = (16 * discounted_total) / 100
        else:
            tax = (3 * discounted_total) / 100
            
        grand_total = tax + discounted_total + shipping_cost
    except ObjectDoesNotExist:
        pass

    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'discount_amount': discount_amount,
        'discounted_total': total - (discount_amount if 'discount_amount' in locals() else 0),
        'coupon_code': request.session.get('coupon_code'),
        'grand_total': grand_total,
        'tax': tax,
        'total_weight': total_weight,
        'shipping_cost': shipping_cost,
    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        total_weight = 0
        shipping_cost = 0
        discount_amount = 0
        coupon_code = request.session.get('coupon_code', None)

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            
        for cart_item in cart_items:
            total+=(cart_item.product.price * cart_item.quantity)
            quantity+=cart_item.quantity
            
        # Calculate shipping
        total_weight, shipping_cost = calculate_shipping(cart_items, total)

        # Apply discount
        if coupon_code:
            is_valid, discount_amount, coupon_obj, coupon_msg = DiscountService.apply_coupon(
                request.user,
                total,
                coupon_code
            )
            if not is_valid:
                request.session['coupon_code'] = None
                discount_amount = 0

        discounted_total = total - discount_amount

        # Pass subtotal without tax - checkout page calculates tax dynamically per payment method
        tax = 0
        grand_total = discounted_total + shipping_cost

        shipping_addresses = []
        if request.user.is_authenticated:
            shipping_addresses = request.user.shipping_addresses.all().order_by('-is_default', '-created_at')

    except ObjectDoesNotExist:
        pass

    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'discount_amount': discount_amount,
        'coupon_code': request.session.get('coupon_code'),
        'grand_total': grand_total,
        'tax': tax,
        'total_weight': total_weight,
        'shipping_cost': shipping_cost,
        'shipping_addresses': shipping_addresses,
    }
    return render(request, 'store/checkout.html', context)

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        if coupon_code:
            request.session['coupon_code'] = coupon_code
            messages.success(request, "Cupón registrado. El descuento se aplicará si cumple las condiciones.")
    return redirect('cart')

def remove_coupon(request):
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        messages.success(request, "Cupón removido.")
    return redirect('cart')
