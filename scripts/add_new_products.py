import os
import django
import shutil
from django.core.files import File

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from store.models import Product
from category.models import Category

# Define the products and their respective images and categories
new_products = [
    {
        "name": "Rollo de Fibra de Vidrio con Aluminio",
        "slug": "rollo-fibra-vidrio-aluminio",
        "category_name": "Aislantes",
        "price": 45,
        "stock": 100,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\fiberglass_roll_1777146302033.png"
    },
    {
        "name": "Panel de Lana de Roca",
        "slug": "panel-lana-roca",
        "category_name": "Aislantes",
        "price": 35,
        "stock": 150,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\rockwool_panel_1777146311457.png"
    },
    {
        "name": "Espuma de Poliuretano en Spray",
        "slug": "espuma-poliuretano-spray",
        "category_name": "Aislantes",
        "price": 12,
        "stock": 200,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\spray_foam_1777146324514.png"
    },
    {
        "name": "Manta de Fibra Cerámica",
        "slug": "manta-fibra-ceramica",
        "category_name": "Aislantes",
        "price": 60,
        "stock": 80,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\ceramic_blanket_1777146338402.png"
    },
    {
        "name": "Placa de Poliestireno Extruido XPS",
        "slug": "placa-poliestireno-extruido-xps",
        "category_name": "Aislantes",
        "price": 25,
        "stock": 120,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\xps_board_1777146350508.png"
    },
    {
        "name": "Ladrillo Refractario de Alta Alúmina",
        "slug": "ladrillo-refractario-alta-alumina",
        "category_name": "Refractarios",
        "price": 5,
        "stock": 500,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\alumina_brick_1777146362561.png"
    },
    {
        "name": "Cemento Refractario Castable",
        "slug": "cemento-refractario-castable",
        "category_name": "Refractarios",
        "price": 40,
        "stock": 100,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_cement_1777146375423.png"
    },
    {
        "name": "Mortero Refractario",
        "slug": "mortero-refractario",
        "category_name": "Refractarios",
        "price": 30,
        "stock": 150,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_mortar_1777146388076.png"
    },
    {
        "name": "Hormigón Aislante Refractario",
        "slug": "hormigon-aislante-refractario",
        "category_name": "Refractarios",
        "price": 45,
        "stock": 90,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\refractory_concrete_1777146400383.png"
    },
    {
        "name": "Ladrillo Aislante Refractario",
        "slug": "ladrillo-aislante-refractario",
        "category_name": "Refractarios",
        "price": 8,
        "stock": 300,
        "image_path": r"C:\Users\ckelv\.gemini\antigravity\brain\bda3a5f9-b453-4bb7-ac49-22efe689eb77\insulating_brick_1777146415154.png"
    }
]

def add_products():
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
                "description": f"Excelente calidad de {prod_data['name'].lower()} para proyectos industriales."
            }
        )
        
        if created or not product.images:
            if os.path.exists(prod_data["image_path"]):
                with open(prod_data["image_path"], 'rb') as f:
                    file_name = os.path.basename(prod_data["image_path"])
                    product.images.save(file_name, File(f), save=True)
                print(f"Created product: {product.product_name} with image.")
            else:
                print(f"Warning: Image not found at {prod_data['image_path']}")
        else:
            print(f"Product already exists: {product.product_name}")

if __name__ == '__main__':
    add_products()
