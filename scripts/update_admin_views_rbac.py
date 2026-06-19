import re

file_path = r'c:\Users\ckelv\Desktop\Ecommerce\accounts\admin_views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports
if 'from accounts.decorators import has_permission' not in content:
    content = content.replace('from accounts.forms import AdminProfileForm', 
                              "from accounts.forms import AdminProfileForm\nfrom accounts.models import Role, Permission\nfrom accounts.decorators import has_permission")

# Add decorators to existing views
content = re.sub(r'(@staff_member_required\(login_url=\'login\'\)\s*def admin_orders\(request\):)', 
                 r"@has_permission('view_orders')\n\1", content)
content = re.sub(r'(@staff_member_required\(login_url=\'login\'\)\s*def admin_products\(request\):)', 
                 r"@has_permission('view_inventory')\n\1", content)
content = re.sub(r'(@staff_member_required\(login_url=\'login\'\)\s*def admin_customers\(request\):)', 
                 r"@has_permission('view_users')\n\1", content)

new_views = """
# ==========================================
# ROLES MANAGEMENT
# ==========================================

@has_permission('view_roles')
def admin_roles(request):
    roles = Role.objects.annotate(user_count=Count('account')).all()
    pending_orders_count = Order.objects.filter(is_ordered=True, status__in=['New', 'Accepted']).count()
    context = {
        'active_page': 'roles',
        'roles': roles,
        'pending_orders_count': pending_orders_count,
    }
    return render(request, 'admin_panel/roles.html', context)

@has_permission('create_roles')
def admin_create_role(request):
    permissions = Permission.objects.all().order_by('module')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        selected_perms = request.POST.getlist('permissions')
        
        if Role.objects.filter(name=name).exists():
            messages.error(request, 'Ya existe un rol con ese nombre.')
        else:
            role = Role.objects.create(name=name, description=description)
            role.permissions.set(selected_perms)
            messages.success(request, 'Rol creado exitosamente.')
            return redirect('admin_roles')
            
    # Group permissions by module for the matrix
    modules = {}
    for p in permissions:
        if p.module not in modules:
            modules[p.module] = []
        modules[p.module].append(p)
        
    pending_orders_count = Order.objects.filter(is_ordered=True, status__in=['New', 'Accepted']).count()
    return render(request, 'admin_panel/role_form.html', {
        'active_page': 'roles',
        'modules': modules,
        'action': 'Crear',
        'pending_orders_count': pending_orders_count
    })

@has_permission('edit_roles')
def admin_edit_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    permissions = Permission.objects.all().order_by('module')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        selected_perms = request.POST.getlist('permissions')
        
        if Role.objects.filter(name=name).exclude(id=role.id).exists():
            messages.error(request, 'Ya existe un rol con ese nombre.')
        else:
            role.name = name
            role.description = description
            role.permissions.set(selected_perms)
            role.save()
            messages.success(request, 'Rol actualizado exitosamente.')
            return redirect('admin_roles')
            
    modules = {}
    for p in permissions:
        if p.module not in modules:
            modules[p.module] = []
        modules[p.module].append(p)
        
    role_perms = role.permissions.values_list('id', flat=True)
        
    pending_orders_count = Order.objects.filter(is_ordered=True, status__in=['New', 'Accepted']).count()
    return render(request, 'admin_panel/role_form.html', {
        'active_page': 'roles',
        'role': role,
        'modules': modules,
        'role_perms': role_perms,
        'action': 'Editar',
        'pending_orders_count': pending_orders_count
    })

@has_permission('delete_roles')
def admin_delete_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        role.delete()
        messages.success(request, 'Rol eliminado.')
    return redirect('admin_roles')

@has_permission('create_roles')
def admin_clone_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        new_name = role.name + " (Copia)"
        i = 1
        while Role.objects.filter(name=new_name).exists():
            new_name = f"{role.name} (Copia {i})"
            i += 1
            
        new_role = Role.objects.create(name=new_name, description=role.description)
        new_role.permissions.set(role.permissions.all())
        messages.success(request, 'Rol duplicado exitosamente. Ahora puedes editarlo.')
        return redirect('admin_edit_role', role_id=new_role.id)
    return redirect('admin_roles')

# ==========================================
# USERS MANAGEMENT
# ==========================================

@has_permission('view_users')
def admin_users(request):
    # Only show staff/admin users or allow seeing all users?
    # Based on the requirement, we show users to manage their roles.
    users = Account.objects.all().order_by('-date_joined')
    pending_orders_count = Order.objects.filter(is_ordered=True, status__in=['New', 'Accepted']).count()
    context = {
        'active_page': 'users',
        'users': users,
        'pending_orders_count': pending_orders_count,
    }
    return render(request, 'admin_panel/users.html', context)

@has_permission('create_users')
def admin_create_user(request):
    from accounts.forms import RegistrationForm
    roles = Role.objects.all()
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.is_active = True # auto activate for admin created users
            
            # If roles are assigned, make them staff
            selected_roles = request.POST.getlist('roles')
            if selected_roles:
                user.is_staff = True
                user.save()
                user.roles.set(selected_roles)
            else:
                user.save()
                
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('admin_users')
    else:
        form = RegistrationForm()
        
    pending_orders_count = Order.objects.filter(is_ordered=True, status__in=['New', 'Accepted']).count()
    return render(request, 'admin_panel/user_form.html', {
        'active_page': 'users',
        'form': form,
        'roles': roles,
        'action': 'Crear',
        'pending_orders_count': pending_orders_count
    })

@has_permission('edit_users')
def admin_edit_user(request, user_id):
    user = get_object_or_404(Account, id=user_id)
    roles = Role.objects.all()
    
    # Superadmin protection
    if user.is_superadmin and not request.user.is_superadmin:
        messages.error(request, 'No tienes permisos para editar a un Super Administrador.')
        return redirect('admin_users')
        
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        is_active = request.POST.get('is_active') == 'on'
        # Prevent deactivating superadmin
        if user.is_superadmin:
            is_active = True
            
        user.is_active = is_active
        
        selected_roles = request.POST.getlist('roles')
        if selected_roles:
            user.is_staff = True
        else:
            if not user.is_superadmin:
                user.is_staff = False
                
        user.save()
        user.roles.set(selected_roles)
        messages.success(request, 'Usuario actualizado exitosamente.')
        return redirect('admin_users')
        
    user_roles = user.roles.values_list('id', flat=True)
    pending_orders_count = Order.objects.filter(is_ordered=True, status__in=['New', 'Accepted']).count()
    return render(request, 'admin_panel/user_form.html', {
        'active_page': 'users',
        'edit_user': user,
        'roles': roles,
        'user_roles': user_roles,
        'action': 'Editar',
        'pending_orders_count': pending_orders_count
    })

@has_permission('delete_users')
def admin_delete_user(request, user_id):
    user = get_object_or_404(Account, id=user_id)
    if request.method == 'POST':
        if user.is_superadmin:
            messages.error(request, 'No puedes eliminar a un Super Administrador.')
        elif user == request.user:
            messages.error(request, 'No puedes eliminarte a ti mismo.')
        else:
            user.delete()
            messages.success(request, 'Usuario eliminado.')
    return redirect('admin_users')

"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content + "\n" + new_views)

print("admin_views.py updated with RBAC views.")
