from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_panel_access_required(view_func):
    """Only superadmins or users with at least one role can access the admin panel."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superadmin:
            return view_func(request, *args, **kwargs)
        if not request.user.is_staff or not request.user.roles.exists():
            messages.error(request, 'No tienes acceso al panel de administración.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def has_permission(codename):
    """Check that user has a specific RBAC permission (superadmins bypass)."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            # Must have at least one role to be in the panel
            if not request.user.is_superadmin and not request.user.roles.exists():
                messages.error(request, 'No tienes acceso al panel de administración.')
                return redirect('home')
            if not request.user.has_rbac_permission(codename):
                messages.error(request, 'No tienes permisos para acceder a este módulo.')
                return redirect('admin_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
