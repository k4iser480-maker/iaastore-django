import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from accounts.models import Permission

permissions_data = [
    # Inventario
    {'module': 'Inventario', 'name': 'Ver', 'codename': 'view_inventory'},
    {'module': 'Inventario', 'name': 'Crear', 'codename': 'create_inventory'},
    {'module': 'Inventario', 'name': 'Editar', 'codename': 'edit_inventory'},
    {'module': 'Inventario', 'name': 'Eliminar', 'codename': 'delete_inventory'},
    {'module': 'Inventario', 'name': 'Exportar', 'codename': 'export_inventory'},
    # Pedidos
    {'module': 'Pedidos', 'name': 'Ver', 'codename': 'view_orders'},
    {'module': 'Pedidos', 'name': 'Crear', 'codename': 'create_orders'},
    {'module': 'Pedidos', 'name': 'Editar', 'codename': 'edit_orders'},
    {'module': 'Pedidos', 'name': 'Eliminar', 'codename': 'delete_orders'},
    {'module': 'Pedidos', 'name': 'Exportar', 'codename': 'export_orders'},
    {'module': 'Pedidos', 'name': 'Aprobar', 'codename': 'approve_orders'},
    {'module': 'Pedidos', 'name': 'Rechazar', 'codename': 'reject_orders'},
    # Usuarios
    {'module': 'Usuarios', 'name': 'Ver', 'codename': 'view_users'},
    {'module': 'Usuarios', 'name': 'Crear', 'codename': 'create_users'},
    {'module': 'Usuarios', 'name': 'Editar', 'codename': 'edit_users'},
    {'module': 'Usuarios', 'name': 'Eliminar', 'codename': 'delete_users'},
    # Roles
    {'module': 'Roles', 'name': 'Ver', 'codename': 'view_roles'},
    {'module': 'Roles', 'name': 'Crear', 'codename': 'create_roles'},
    {'module': 'Roles', 'name': 'Editar', 'codename': 'edit_roles'},
    {'module': 'Roles', 'name': 'Eliminar', 'codename': 'delete_roles'},
    # Reportes
    {'module': 'Reportes', 'name': 'Ver', 'codename': 'view_reports'},
    # Respaldos
    {'module': 'Respaldos', 'name': 'Ver', 'codename': 'view_backups'},
    {'module': 'Respaldos', 'name': 'Gestionar', 'codename': 'manage_backups'},
    # Transportistas
    {'module': 'Transportistas', 'name': 'Acceso a Interfaz', 'codename': 'access_transportista_panel'},
]

for p_data in permissions_data:
    Permission.objects.update_or_create(
        codename=p_data['codename'], 
        defaults={
            'module': p_data['module'],
            'name': p_data['name']
        }
    )

print("Permissions seeded successfully.")
