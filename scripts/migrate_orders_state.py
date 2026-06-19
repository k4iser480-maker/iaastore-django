import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecosite.settings")
django.setup()

from orders.models import Order

def run():
    orders = Order.objects.all()
    count = 0
    for order in orders:
        if order.is_ordered:
            order.payment_status = 'paid'
            # Update logistic status if it was in an old state
            if order.status in ['Accepted', 'pendiente', 'New']:
                order.status = 'Processing'
            elif order.status == 'asignado':
                order.status = 'Assigned'
            elif order.status == 'en_camino':
                order.status = 'In Transit'
            elif order.status == 'entregado':
                order.status = 'Delivered'
        else:
            order.payment_status = 'pending'
            order.status = 'New'
        order.save()
        count += 1
    
    print(f"Migrated {count} orders successfully.")

if __name__ == '__main__':
    run()
