import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecosite.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from accounts.models import Account
from orders.views import payments
from orders.models import Order

# Find a pending order to test
order = Order.objects.filter(payment_status='pending').first()
if not order:
    print("No pending orders found.")
else:
    user = order.user
    factory = RequestFactory()
    
    data = {
        'orderID': order.order_number,
        'transID': 'TEST12345',
        'payment_method': 'PayPal',
        'status': 'COMPLETED',
    }
    
    request = factory.post('/orders/payments/', data=json.dumps(data), content_type='application/json')
    request.user = user
    
    try:
        response = payments(request)
        print("Response status:", response.status_code)
        print("Response content:", response.content)
    except Exception as e:
        import traceback
        traceback.print_exc()
