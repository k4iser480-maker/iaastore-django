import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecosite.settings")
django.setup()

from django.test import Client
from orders.models import Order

# Find a pending order to test
order = Order.objects.filter(payment_status='pending').first()
if not order:
    print("No pending orders found.")
else:
    user = order.user
    client = Client()
    client.force_login(user)
    
    data = {
        'orderID': order.order_number,
        'transID': 'TEST12345',
        'payment_method': 'PayPal',
        'status': 'COMPLETED',
    }
    
    response = client.post('/orders/payments/', data=json.dumps(data), content_type='application/json')
    print("Response status:", response.status_code)
    print("Response content:", response.content.decode('utf-8')[:500])
