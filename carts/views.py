from django.shortcuts import render
from store.models import Product
from .models import Cart, CartItem
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

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
    
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        # create a new item and save it
        cart_item = CartItem.objects.create(product=product, cart=cart, quantity=1, user=request.user if request.user.is_authenticated else None)
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
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total+=(cart_item.product.price * cart_item.quantity)
            quantity+=cart_item.quantity
        tax = (2 * total) / 100
        grand_total = tax + total
    except ObjectDoesNotExist:
        pass

    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax': tax
    }
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total+=(cart_item.product.price * cart_item.quantity)
            quantity+=cart_item.quantity
        tax = (2 * total) / 100
        grand_total = tax + total
    except ObjectDoesNotExist:
        pass

    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax': tax
    }
    return render(request, 'store/checkout.html', context)
