import os
import django
import shutil
from django.core.files import File

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from store.models import Product

prod_data = {
    "name": "Mortero Refractario",
    "slug": "mortero-refractario",
    "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_mortar_1777146388076.png"
}

try:
    product = Product.objects.get(slug=prod_data["slug"])
    if os.path.exists(prod_data["image_path"]):
        with open(prod_data["image_path"], 'rb') as f:
            file_name = os.path.basename(prod_data["image_path"])
            product.images.save(file_name, File(f), save=True)
        print(f"Updated product image for: {product.product_name}")
    else:
        print(f"Warning: Image not found at {prod_data['image_path']}")
except Product.DoesNotExist:
    print("Product not found.")
