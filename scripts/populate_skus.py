import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from store.models import Product

def populate_skus():
    products = Product.objects.all()
    count = 0
    for product in products:
        if not product.sku:
            product.sku = product._generate_sku()
            product.save(update_fields=['sku'])
            count += 1
            print(f"Generated SKU for {product.product_name}: {product.sku}")
    print(f"Total SKUs generated: {count}")

if __name__ == '__main__':
    populate_skus()
