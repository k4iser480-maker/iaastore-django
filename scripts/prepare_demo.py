from accounts.models import Account, ShippingAddress
from store.models import Product
from orders.models import Order, OrderProduct, DeliveryCheckpoint, DeliveryStatus, Transportista
from django.utils import timezone

# 1. DELETE KELVIN CAMACHO'S REPETITIVE ORDERS
admin_user = Account.objects.filter(is_superadmin=True).first()
if admin_user:
    Order.objects.filter(user=admin_user).delete()
    print("Deleted orders for administrator:", admin_user.email)

# 2. IDENTIFY FILLER ACCOUNTS AND CLEAN THEIR ORDERS
filler_users = Account.objects.filter(is_superadmin=False).exclude(id__in=Transportista.objects.values('user_id')).order_by('id')[:10]
print(f"Found {filler_users.count()} filler accounts.")

for u in filler_users:
    Order.objects.filter(user=u).delete()

products = list(Product.objects.filter(is_available=True)[:3])
transportistas = list(Transportista.objects.all())
transp1 = transportistas[0] if len(transportistas) > 0 else None
transp2 = transportistas[1] if len(transportistas) > 1 else None

def create_order(user, status, payment_status, is_test=False, trans=None, order_note=''):
    addr = ShippingAddress.objects.filter(user=user).first()
    o = Order.objects.create(
        user=user,
        order_number=f"{timezone.now().strftime('%Y%m%d')}", # Will append id later
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone_number or "04141234567",
        email=user.email,
        address_line_1=addr.address_line_1 if addr else "Calle de Prueba, 123",
        city=addr.city if addr else "Barcelona",
        state=addr.state if addr else "Anzoategui",
        order_total=100.0,
        tax=16.0,
        status=status,
        payment_status=payment_status,
        is_test=is_test,
        transportista=trans,
        order_note=order_note
    )
    if products:
        OrderProduct.objects.create(
            order=o,
            user=user,
            product=products[0],
            quantity=1,
            product_price=products[0].price
        )
    
    # Fix order_number protocol
    o.order_number = f"{timezone.now().strftime('%Y%m%d')}{o.id}"
    o.save()
    
    return o

demo_data = [
    {'status': 'Cancelled', 'pay': 'failed', 'trans': None, 'note': 'Ejemplo de cancelado'},
    {'status': 'review', 'pay': 'review', 'trans': None, 'note': 'Ejemplo pago en revisión'}, # using 'review' status, which might just map to payment_status='review' in real logic, but let's just force it
    {'status': 'Processing', 'pay': 'paid', 'trans': None, 'note': 'Ejemplo procesando'},
    {'status': 'Assigned', 'pay': 'paid', 'trans': transp1, 'note': 'Ejemplo asignado'},
    {'status': 'In Transit', 'pay': 'paid', 'trans': transp2, 'note': 'Ejemplo en camino'},
    {'status': 'Delivered', 'pay': 'paid', 'trans': transp1, 'note': 'Ejemplo entregado'},
    {'status': 'Completed', 'pay': 'paid', 'trans': None, 'note': 'Ejemplo completado'}
]

print("Creating demo orders...")
for i, data in enumerate(demo_data):
    if i < len(filler_users):
        u = filler_users[i]
        o = create_order(u, data['status'], data['pay'], trans=data['trans'], order_note=data['note'])
        
        if data['status'] == 'Picked Up':
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.PICKED_UP)
        elif data['status'] == 'In Transit':
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.PICKED_UP)
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.IN_TRANSIT)
        elif data['status'] == 'Delivered':
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.PICKED_UP)
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.IN_TRANSIT)
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.NEARBY)
            DeliveryCheckpoint.objects.create(order=o, status=DeliveryStatus.DELIVERED)
            o.fecha_entrega = timezone.now()
            o.save()

if transp1:
    transp1.disponible = True
    transp1.save()
if transp2:
    transp2.disponible = False
    transp2.save()

print("Database prepared for demo successfully.")
