
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from store.models import Product

def populate():
    products = Product.objects.all()
    units = ['cm', 'm']
    
    for product in products:
        # Generate some realistic-ish data
        # If it's a small item, use cm. If it's something like an 'angulo', maybe m.
        
        if 'angulo' in product.product_name.lower() or 'tubo' in product.product_name.lower():
            unit = 'm'
            length = random.uniform(2.0, 6.0)
            width = random.uniform(0.05, 0.2)
            height = random.uniform(0.05, 0.2)
            weight = random.uniform(5.0, 50.0)
        else:
            unit = 'cm'
            length = random.uniform(10.0, 100.0)
            width = random.uniform(10.0, 80.0)
            height = random.uniform(5.0, 50.0)
            weight = random.uniform(0.5, 20.0)
            
        product.gross_weight = round(weight, 2)
        product.length = round(length, 2)
        product.length_unit = unit
        product.width = round(width, 2)
        product.width_unit = unit
        product.height = round(height, 2)
        product.height_unit = unit
        
        product.save()
        print(f"Updated {product.product_name}: {product.gross_weight}kg, {product.length}{product.length_unit} x {product.width}{product.width_unit} x {product.height}{product.height_unit}")

if __name__ == '__main__':
    populate()
