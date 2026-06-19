import os
import django
from django.core.files import File

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from store.models import Product
from category.models import Category

# Delete the redundant bricks
redundant_slugs = [
    'ladrillo-refractario-alta-alumina',
    'ladrillo-aislante-refractario'
]

for slug in redundant_slugs:
    try:
        prod = Product.objects.get(slug=slug)
        prod.delete()
        print(f"Deleted product: {slug}")
    except Product.DoesNotExist:
        pass

# Add new varied products
new_products = [
    {
        "name": "Crisol de Grafito y Arcilla",
        "slug": "crisol-grafito-arcilla",
        "category_name": "Refractarios",
        "price": 85,
        "stock": 40,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\graphite_crucible_1777148496651.png"
    },
    {
        "name": "Placa de Cerámica Refractaria",
        "slug": "placa-ceramica-refractaria",
        "category_name": "Refractarios",
        "price": 55,
        "stock": 100,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\ceramic_plate_1777148512057.png"
    },
    {
        "name": "Tubos Refractarios",
        "slug": "tubos-refractarios",
        "category_name": "Refractarios",
        "price": 25,
        "stock": 200,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_tubes_1777148526484.png"
    },
    {
        "name": "Masilla Refractaria para Sellado",
        "slug": "masilla-refractaria-sellado",
        "category_name": "Refractarios",
        "price": 15,
        "stock": 300,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_putty_1777148539442.png"
    },
    {
        "name": "Pintura o Recubrimiento Refractario",
        "slug": "pintura-recubrimiento-refractario",
        "category_name": "Refractarios",
        "price": 65,
        "stock": 80,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_coating_1777148554410.png"
    }
]

def add_new_varied_products():
    for prod_data in new_products:
        try:
            category = Category.objects.get(category_name=prod_data["category_name"])
        except Category.DoesNotExist:
            print(f"Error: Category '{prod_data['category_name']}' not found.")
            continue
            
        product, created = Product.objects.get_or_create(
            slug=prod_data["slug"],
            defaults={
                "product_name": prod_data["name"],
                "price": prod_data["price"],
                "stock": prod_data["stock"],
                "Category": category,
                "is_available": True,
                "description": f"Excelente calidad de {prod_data['name'].lower()} para uso en altas temperaturas."
            }
        )
        
        if created or not product.images:
            if os.path.exists(prod_data["image_path"]):
                with open(prod_data["image_path"], 'rb') as f:
                    file_name = os.path.basename(prod_data["image_path"])
                    product.images.save(file_name, File(f), save=True)
                print(f"Created product: {product.product_name}")
            else:
                print(f"Warning: Image not found at {prod_data['image_path']}")
        else:
            print(f"Product already exists: {product.product_name}")

if __name__ == '__main__':
    add_new_varied_products()
