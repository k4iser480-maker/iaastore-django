"""
Seed script: Generate demo orders with proper state machine states.
Clears all existing orders first, then creates realistic test data.
"""
import os, sys, random, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')

import django
django.setup()

from django.utils import timezone
from accounts.models import Account
from orders.models import Order, OrderProduct, Payment, Transportista
from store.models import Product

# ===== CONFIG =====
FAKE_CUSTOMERS = [
    {'first_name': 'Ana',     'last_name': 'Rodriguez', 'email': 'ana.rodriguez@demo.com'},
    {'first_name': 'Miguel',  'last_name': 'Torres',    'email': 'miguel.torres@demo.com'},
    {'first_name': 'Sofia',   'last_name': 'Martinez',  'email': 'sofia.martinez@demo.com'},
    {'first_name': 'Carlos',  'last_name': 'Hernandez', 'email': 'carlos.hernandez@demo.com'},
    {'first_name': 'Lucia',   'last_name': 'Gomez',     'email': 'lucia.gomez@demo.com'},
]

PAYMENT_METHODS = ['PayPal', 'Zelle', 'Pago Movil', 'Cashea']

CITIES = [
    ('Barcelona', 'Anzoátegui'),
    ('Lechería', 'Anzoátegui'),
]

# ===== STEP 1: Clear existing orders =====
print("Eliminando pedidos existentes...")
OrderProduct.objects.all().delete()
Payment.objects.all().delete()
Order.objects.all().delete()
print("  ✓ Todos los pedidos eliminados.")

# ===== STEP 2: Create/get fake customer accounts =====
print("\nCreando cuentas de clientes ficticios...")
customers = []
for c in FAKE_CUSTOMERS:
    user, created = Account.objects.get_or_create(
        email=c['email'],
        defaults={
            'first_name': c['first_name'],
            'last_name': c['last_name'],
            'username': c['email'].split('@')[0],
            'is_active': True,
        }
    )
    if created:
        user.set_password('Demo1234!')
        user.save()
        print(f"  + Creado: {user.first_name} {user.last_name} ({user.email})")
    else:
        print(f"  = Existente: {user.first_name} {user.last_name} ({user.email})")
    customers.append(user)

# ===== STEP 3: Get available data =====
products = list(Product.objects.all())
transportistas = list(Transportista.objects.all())

if not products:
    print("\n❌ No hay productos. Abortando.")
    sys.exit(1)

# ===== STEP 4: Define orders to create =====
# Each entry: (is_delivery, target_payment_status, target_order_status, transportista_index_or_None, days_ago, payment_method)
ORDER_CONFIGS = [
    # === PENDIENTES / EN REVISIÓN ===
    (False, 'pending', 'New', None, 1, 'PayPal'), # Abandonado en checkout
    (True,  'review',  'New', None, 0, 'Pago Movil'), # Esperando verificación admin
    (True,  'review',  'New', None, 1, 'Zelle'), # Esperando verificación admin

    # === SIN DELIVERY ===
    # Processing (recien pagado, sin delivery)
    (False, 'paid', 'Processing',  None, 1, 'PayPal'),
    (False, 'paid', 'Processing',  None, 2, 'Zelle'),
    # Completed (sin delivery, ya completado)
    (False, 'paid', 'Completed', None, 10, 'PayPal'),
    (False, 'paid', 'Completed', None, 8,  'Pago Movil'),
    # Cancelled (sin delivery)
    (False, 'failed', 'Cancelled', None, 5,  'Zelle'),

    # === CON DELIVERY ===
    # Processing (pagado, esperando asignación)
    (True, 'paid', 'Processing', None, 1, 'Cashea'),
    (True, 'paid', 'Processing', None, 2, 'Pago Movil'),
    # Assigned (transportista asignado)
    (True, 'paid', 'Assigned',  0, 3, 'Zelle'),
    (True, 'paid', 'Assigned',  1, 2, 'PayPal'),
    # In Transit (transportista en ruta)
    (True, 'paid', 'In Transit', 0, 4, 'Pago Movil'),
    # Delivered (transportista entregó, esperando confirmación del cliente)
    (True, 'paid', 'Delivered', 1, 6, 'Cashea'),
    (True, 'paid', 'Delivered', 2, 5, 'PayPal'),
    # Completed (delivery completado)
    (True, 'paid', 'Completed', 2, 15, 'Zelle'),
    # Cancelled (delivery cancelado antes de envío)
    (True, 'failed', 'Cancelled', None, 7, 'Pago Movil'),
]

# ===== STEP 5: Create orders =====
print(f"\nCreando {len(ORDER_CONFIGS)} pedidos de demostración...")

for i, (is_delivery, target_payment_status, target_order_status, trans_idx, days_ago, pay_method) in enumerate(ORDER_CONFIGS):
    customer = customers[i % len(customers)]
    product = products[i % len(products)]
    qty = random.randint(1, 3)
    
    city, state = random.choice(CITIES) if is_delivery else ('Barcelona', 'Anzoátegui')
    
    # Calculate prices
    subtotal = float(product.price) * qty
    shipping = 5.0 if is_delivery and subtotal < 500 else 0.0
    
    # Tax based on payment method
    if pay_method in ('Pago Movil', 'Cashea'):
        tax = round(subtotal * 0.16, 2)
        igtf = 0
    elif pay_method in ('Zelle', 'PayPal'):
        tax = 0
        igtf = round(subtotal * 0.03, 2)
    else:
        tax = 0
        igtf = 0
    
    payment_fee = round((subtotal + shipping + igtf + 0.30) / (1 - 0.054) - (subtotal + shipping + igtf), 2) if pay_method == 'PayPal' else 0
    
    order_total = round(subtotal + shipping + tax + igtf + payment_fee, 2)
    
    created_at = timezone.now() - datetime.timedelta(days=days_ago, hours=random.randint(1, 12))
    
    # Create payment
    payment = Payment.objects.create(
        user=customer,
        payment_id=f'DEMO-{i+1:04d}',
        payment_method=pay_method,
        status='Completado',
        amount_paid=order_total,
    )
    
    # Create order
    order = Order(
        user=customer,
        payment=payment,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone='0412' + str(random.randint(1000000, 9999999)),
        email=customer.email,
        address_line_1=f'Calle {random.randint(1,50)}, Edif. {random.choice(["Las Palmas", "Sol", "Marina", "Centro", "Valle"])}',
        address_line_2=f'Piso {random.randint(1,10)}, Apto {random.randint(1,20)}' if is_delivery else '',
        state=state,
        city=city,
        order_note='Entregar en horario de oficina' if is_delivery and random.random() > 0.5 else '',
        order_total=order_total,
        tax=tax,
        igtf_tax=igtf,
        payment_fee=payment_fee,
        shipping_cost=shipping,
        is_delivery=is_delivery,
        payment_status=target_payment_status,
        status=target_order_status,
        ip='127.0.0.1',
    )
    order.save()
    
    # Set created_at (bypass auto_now_add)
    Order.objects.filter(id=order.id).update(created_at=created_at)
    
    # Generate order number
    order.order_number = created_at.strftime('%Y%m%d') + str(order.id)
    
    # Assign transportista if needed
    if trans_idx is not None and trans_idx < len(transportistas):
        order.transportista = transportistas[trans_idx]
    
    # Set fecha_entrega for entregado/Completed delivery orders
    if target_order_status == 'Delivered':
        order.fecha_entrega = created_at + datetime.timedelta(days=1)
    elif target_order_status == 'Completed' and is_delivery:
        order.fecha_entrega = created_at + datetime.timedelta(days=2)
    
    order.save()
    
    # Create order product
    OrderProduct.objects.create(
        order=order,
        payment=payment,
        user=customer,
        product=product,
        quantity=qty,
        product_price=product.price,
        ordered=True,
    )
    
    delivery_str = "🚚 delivery" if is_delivery else "🏪 retiro"
    trans_str = f" → {order.transportista.user.first_name}" if order.transportista else ""
    print(f"  #{order.order_number} | {customer.first_name:8s} | {target_payment_status:8s} | {target_order_status:12s} | {delivery_str} | {pay_method:12s} | ${order_total:>8.2f}{trans_str}")

# Update transportista availability based on assigned orders
print("\nActualizando disponibilidad de transportistas...")
for t in transportistas:
    has_active = Order.objects.filter(
        transportista=t,
        status__in=['Assigned', 'In Transit']
    ).exists()
    t.disponible = not has_active
    t.save()
    status_str = "🔴 Ocupado" if has_active else "🟢 Disponible"
    print(f"  {t.user.first_name}: {status_str}")

print(f"\n✅ {len(ORDER_CONFIGS)} pedidos creados exitosamente.")
print("   Resumen de estados logísticos:")
for status in ['New', 'Processing', 'Assigned', 'In Transit', 'Delivered', 'Completed', 'Cancelled']:
    count = Order.objects.filter(status=status).count()
    if count:
        print(f"   • {status}: {count}")
print("   Resumen de estados de pago:")
for p_status in ['pending', 'review', 'paid', 'failed']:
    count = Order.objects.filter(payment_status=p_status).count()
    if count:
        print(f"   • Pago {p_status}: {count}")
