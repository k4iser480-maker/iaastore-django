from store.models import Product
from django.utils.text import slugify

new_names = {
    7: 'Ángulos 1" x 1" x 6m',
    8: 'Barras cuadradas 1/2" x 6m',
    9: 'Flanches Slip-on 4" 150 lbs',
    10: 'Mallas Electrosoldadas 4x4 mm 2.40x4.80m',
    11: 'Ladrillos Refractarios 9x4.5x2.5"', # User mentioned maybe not needed, but bricks definitely have standard sizes. Let's just leave it as 'Ladrillos Refractarios' to follow his suggestion.
    13: 'Vigas doble T IPE 100 x 6m',
    14: 'Viga UPM 100 x 6m',
    15: 'Tubos de acero al carbono 2" x 6m',
    16: 'Saco de cal 20kg',
    17: 'Membrana asfáltica 3.2mm x 10m',
    19: 'Rollo de alambre recocido Calibre 18',
    20: 'Lámina Galvanizada Calibre 20 1.20x2.40m'
}

# I will revert Ladrillos to original if it's strictly not needed, but wait: he said "tal vez los ladrillos o los aislantes que se aplican, no, no aplica la medida". So I'll remove 11.

new_names = {
    7: 'Ángulos 1" x 1" x 6m',
    8: 'Barras cuadradas 1/2" x 6m',
    9: 'Flanches Slip-on 4" 150 lbs',
    10: 'Mallas Electrosoldadas 4x4 mm 2.40x4.80m',
    13: 'Vigas doble T IPE 100 x 6m',
    14: 'Viga UPM 100 x 6m',
    15: 'Tubos de acero al carbono 2" x 6m',
    16: 'Saco de cal 20kg',
    17: 'Membrana asfáltica 3.2mm x 10m',
    19: 'Rollo de alambre Calibre 18',
    20: 'Lámina Galvanizada Calibre 20 1.20x2.40m'
}

for pid, new_name in new_names.items():
    try:
        product = Product.objects.get(id=pid)
        product.product_name = new_name
        product.slug = slugify(new_name)
        product.save()
        print(f"Updated product ID {pid} to: {new_name}")
    except Product.DoesNotExist:
        print(f"Product ID {pid} not found.")
    except Exception as e:
        print(f"Error on ID {pid}: {e}")

print("Name update completed.")
