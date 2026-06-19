from django.shortcuts import render
from carts.models import CartItem
from .forms import OrderForm
import datetime
import json
from .models import Order, Payment, OrderProduct
from django.shortcuts import redirect
from django.http import JsonResponse
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from store.shipping_utils import calculate_shipping
from orders.services.discount_service import DiscountService
from orders.services.referral_service import ReferralService

def payments(request):
    body = json.loads(request.body)
    try:
        order = Order.objects.filter(user=request.user, payment_status='pending', order_number=body['orderID']).latest('created_at')
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado'}, status=400)

    if body['payment_method'] == 'PayPal':
        subtotal = order.order_total - order.shipping_cost
        igtf = subtotal * 0.03
        total_with_igtf = order.order_total + igtf
        final_total = (total_with_igtf + 0.30) / (1 - 0.054)
        fee = final_total - total_with_igtf
        
        order.tax = 0
        order.igtf_tax = round(igtf, 2)
        order.payment_fee = round(fee, 2)
        order.order_total = round(final_total, 2)

    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        status = body['status'],
        amount_paid = order.order_total,
    )
    payment.save()

    payment.save()

    order.payment = payment
    order.payment_status = 'paid'
    order.status = 'Processing'
    order.save()

    # Process referral reward if any
    ReferralService.reward_referral(order)

    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        if not order.is_test:
            product=Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

    CartItem.objects.filter(user=request.user).delete()
    
    # Record coupon usage if there's a coupon on the order
    if order.coupon:
        DiscountService.record_usage(request.user, order.coupon, order)

    # Email
    if not order.is_test:
        from django.contrib.sites.shortcuts import get_current_site
        current_site = get_current_site(request)
        mail_subject = 'Gracias por tu compra'
        message = render_to_string('orders/order_received_email.html', {
                    'user': request.user,
                    'order': order,
                    'domain': current_site.domain,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        try:
            send_email.send()
        except Exception as e:
            print("Error sending order email:", e)

    data={
        'order_number': order.order_number,
        'transID': payment.payment_id,
        }

    return JsonResponse(data)

def manual_payment(request):
    if request.method == 'POST':
        orderID = request.POST.get('orderID')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')
        receipt = request.FILES.get('receipt')

        try:
            order = Order.objects.filter(user=request.user, payment_status='pending', order_number=orderID).latest('created_at')
        except Order.DoesNotExist:
            return redirect('store')

        if payment_method == 'Zelle':
            subtotal = order.order_total - order.shipping_cost
            igtf = subtotal * 0.03
            order.igtf_tax = round(igtf, 2)
            order.tax = 0
            order.order_total = round(order.order_total + igtf, 2)
        elif payment_method in ('Pago Movil', 'Cashea'):
            subtotal = order.order_total - order.shipping_cost
            iva = subtotal * 0.16
            order.tax = round(iva, 2)
            order.igtf_tax = 0
            order.order_total = round(order.order_total + iva, 2)

        payment = Payment(
            user = request.user,
            payment_id = 'Manual',
            payment_method = payment_method,
            status = status,
            amount_paid = order.order_total,
            receipt = receipt
        )
        payment.save()

        order.payment = payment
        order.payment_status = 'review'
        order.status = 'New'
        order.save()
        
        # Note: We do NOT process referral reward here because the payment is manual and not yet confirmed.
        # It will be processed in the admin_update_order_status view when status becomes 'paid'.

        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            if not order.is_test:
                product=Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

        CartItem.objects.filter(user=request.user).delete()

        if not order.is_test:
            from django.contrib.sites.shortcuts import get_current_site
            current_site = get_current_site(request)
            mail_subject = 'Gracias por tu compra'
            message = render_to_string('orders/order_received_email.html', {
                        'user': request.user,
                        'order': order,
                        'domain': current_site.domain,
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

        data={
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment_method': payment.payment_method,
        }

        return JsonResponse(data)

def cashea_success(request):
    order_number = request.GET.get('order_number')
    try:
        order = Order.objects.get(order_number=order_number)
        if order.payment_status == 'pending':
            raise Order.DoesNotExist
    except Order.DoesNotExist:
        return redirect('store')

    return render(request, 'orders/cashea_success.html', {'order': order})

def place_order(request, total=0, quantity=0):
    current_user = request.user

    #if the cart count is less than or equal to 0, then redirect to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'multipart/form-data':
            return JsonResponse({'error': 'El carrito está vacío'}, status=400)
        return redirect('store')
    
    grand_total = 0
    tax = 0
    total_weight = 0
    shipping_cost = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
        
    total_weight, shipping_cost = calculate_shipping(cart_items, total)

    # Apply Coupon
    discount_amount = 0
    coupon_obj = None
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        is_valid, discount_amount, coupon_obj, msg = DiscountService.apply_coupon(
            request.user, total, coupon_code
        )
        if not is_valid:
            discount_amount = 0
            coupon_obj = None

    discounted_total = total - discount_amount

    # Store subtotal only - tax (IVA or IGTF) gets applied during payment processing
    # based on the selected payment method
    tax = 0
    grand_total = discounted_total + shipping_cost
    
    if request.method == 'POST':
        form=OrderForm(request.POST)
        
        is_delivery = request.POST.get('is_delivery') == 'on'
        shipping_address_id = request.POST.get('shipping_address_id')
        
        if not is_delivery:
            shipping_cost = 0
            grand_total = total
            
        if form.is_valid():
            #store all the billing information inside the order table
            data = Order()
            data.user = current_user
            data.is_test = current_user.creates_sandbox_orders
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.shipping_cost = shipping_cost
            data.is_delivery = is_delivery
            data.discount_amount = discount_amount
            if coupon_obj:
                data.coupon = coupon_obj
            
            
            if is_delivery and shipping_address_id:
                from accounts.models import ShippingAddress
                try:
                    address = ShippingAddress.objects.get(id=shipping_address_id, user=current_user)
                    data.shipping_address = address
                except ShippingAddress.DoesNotExist:
                    pass
            
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            #generate order number

            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d") #20240611
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            # Return JSON for AJAX requests (single-page checkout)
            return JsonResponse({
                'order_number': order_number,
                'grand_total': grand_total,
            })
        else:
            return JsonResponse({'error': 'Datos del formulario inválidos'}, status=400)
    else:
        return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    try:
        order = Order.objects.get(order_number=order_number)
        if order.payment_status == 'pending':
            raise Exception("Order not complete")
        payment = order.payment
    except Exception:
        return redirect('store')

    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'orders/order_complete.html', context)

def payment_method_instructions(request, method, order_number):
    try:
        order = Order.objects.filter(user=request.user, payment_status='pending', order_number=order_number).latest('created_at')
    except Order.DoesNotExist:
        return redirect('store')

    subtotal = order.order_total - order.shipping_cost
    display_total = order.order_total
    if method == 'zelle':
        display_total = round(order.order_total + (subtotal * 0.03), 2)
    elif method in ('pagomovil', 'cashea'):
        display_total = round(order.order_total + (subtotal * 0.16), 2)

    context = {
        'order': order,
        'method': method,
        'display_total': display_total,
    }
    return render(request, 'orders/payment_method_instructions.html', context)