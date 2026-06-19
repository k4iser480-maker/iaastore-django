import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from accounts.models import Account

try:
    user = Account.objects.get(email='ecosite@gmail.com')
    user.is_superadmin = True
    user.is_admin = True
    user.is_staff = True
    user.role = 'admin'
    user.save()
    print(f"Success: User {user.email} updated to superadmin with role 'admin'.")
except Account.DoesNotExist:
    print("Error: User ecosite@gmail.com does not exist.")
