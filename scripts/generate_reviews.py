import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from store.models import Product, ReviewRating
from accounts.models import Account

def generate_reviews():
    # Fake user details
    fake_users = [
        {"first_name": "Juan", "last_name": "Perez", "username": "juanp", "email": "juan@example.com"},
        {"first_name": "Maria", "last_name": "Gomez", "username": "mariag", "email": "maria@example.com"},
        {"first_name": "Carlos", "last_name": "Lopez", "username": "carlosl", "email": "carlos@example.com"},
        {"first_name": "Ana", "last_name": "Martinez", "username": "anam", "email": "ana@example.com"},
        {"first_name": "Luis", "last_name": "Rodriguez", "username": "luisr", "email": "luis@example.com"},
        {"first_name": "Pedro", "last_name": "Sanchez", "username": "pedros", "email": "pedro@example.com"},
        {"first_name": "Elena", "last_name": "Ramirez", "username": "elenar", "email": "elena@example.com"},
        {"first_name": "Miguel", "last_name": "Fernandez", "username": "miguelf", "email": "miguel@example.com"},
    ]
    
    # Create or get users
    accounts = []
    for u_data in fake_users:
        user, created = Account.objects.get_or_create(
            email=u_data["email"],
            defaults={
                "first_name": u_data["first_name"],
                "last_name": u_data["last_name"],
                "username": u_data["username"],
                "phone_number": "1234567890",
                "is_active": True,
            }
        )
        if created:
            user.set_password("password123")
            user.save()
        accounts.append(user)

    reviews_data = [
        {"subject": "Excelente producto", "review": "Me encantó, la calidad es súper buena y llegó a tiempo. Totalmente recomendado.", "rating": 5.0},
        {"subject": "Muy bueno", "review": "Cumple con lo que promete. La relación calidad-precio es excelente.", "rating": 4.5},
        {"subject": "Buen producto", "review": "Todo bien, funciona como se espera, pero podría mejorar algunos detalles.", "rating": 4.0},
        {"subject": "Me gusta", "review": "Estoy satisfecho con la compra. El producto es de buena calidad.", "rating": 5.0},
        {"subject": "Recomendado", "review": "Lo compré hace unos días y hasta ahora todo excelente. Muy buena atención.", "rating": 4.5},
        {"subject": "Fantástico", "review": "Superó mis expectativas. Lo recomiendo al 100%.", "rating": 5.0},
        {"subject": "Normal", "review": "Es un buen producto, cumple su función correctamente.", "rating": 3.5},
        {"subject": "Increíble calidad", "review": "No esperaba que fuera tan bueno. Definitivamente volveré a comprar.", "rating": 5.0},
        {"subject": "Muy útil", "review": "Me ha servido muchísimo, es justo lo que necesitaba.", "rating": 4.5},
        {"subject": "Buena compra", "review": "Llegó rápido y en perfectas condiciones. Muy contento con el servicio.", "rating": 5.0},
    ]

    products = Product.objects.all()
    
    count = 0
    for product in products:
        num_reviews = random.randint(3, 5)
        users = random.sample(accounts, num_reviews)
        
        for user in users:
            # Check if review already exists
            if not ReviewRating.objects.filter(product=product, user=user).exists():
                review_choice = random.choice(reviews_data)
                ReviewRating.objects.create(
                    product=product,
                    user=user,
                    subject=review_choice["subject"],
                    review=review_choice["review"],
                    rating=review_choice["rating"],
                    ip="127.0.0.1",
                    status=True
                )
                count += 1
                
    print(f"Generated {count} reviews.")

if __name__ == '__main__':
    generate_reviews()
