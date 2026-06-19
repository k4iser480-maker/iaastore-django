import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecosite.settings")
django.setup()

from accounts.models import Account, Role, Permission
from orders.models import Transportista

def seed():
    # 1. Create or get the 'access_transportista_panel' permission
    perm, _ = Permission.objects.get_or_create(
        codename='access_transportista_panel',
        defaults={'name': 'Acceso a Interfaz', 'module': 'Transportistas'}
    )

    # 2. Create the 'Transportista' role
    role, created = Role.objects.get_or_create(
        name='Transportista',
        defaults={'description': 'Rol para transportistas encargados del delivery'}
    )
    if created:
        role.permissions.add(perm)
        print("Rol 'Transportista' creado y permiso 'access_transportista_panel' asignado.")
    else:
        role.permissions.add(perm)
        print("Rol 'Transportista' ya existía. Permiso asegurado.")

    # 3. Create 3 Transportistas
    transportistas_data = [
        {'first_name': 'Carlos', 'last_name': 'Mendoza', 'username': 'cmendoza', 'email': 'cmendoza@transporte.com', 'telefono': '0414-1112233', 'vehiculo': 'Moto Empire 150'},
        {'first_name': 'Luis', 'last_name': 'Perez', 'username': 'lperez', 'email': 'lperez@transporte.com', 'telefono': '0412-4445566', 'vehiculo': 'Furgoneta Renault'},
        {'first_name': 'Pedro', 'last_name': 'Gomez', 'username': 'pgomez', 'email': 'pgomez@transporte.com', 'telefono': '0416-7778899', 'vehiculo': 'Moto Bera 200'},
    ]

    for data in transportistas_data:
        # Create User
        if not Account.objects.filter(email=data['email']).exists():
            user = Account.objects.create_user(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                username=data['username'],
                password='Password123!'
            )
            user.is_active = True
            user.is_staff = True  # Required to access custom admin panel
            user.save()
            user.roles.add(role)
            print(f"Usuario {user.email} creado y asignado al rol Transportista.")

            # Create Transportista profile
            Transportista.objects.create(
                user=user,
                telefono=data['telefono'],
                vehiculo=data['vehiculo'],
                email_notificaciones='k4iser480@gmail.com'
            )
            print(f"Perfil de transportista creado para {user.email}.")
        else:
            print(f"El usuario {data['email']} ya existe.")

if __name__ == '__main__':
    seed()
