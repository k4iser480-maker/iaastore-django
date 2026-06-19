from django import template

register = template.Library()

@register.filter(name='can')
def can(user, codename):
    if not user.is_authenticated:
        return False
    return user.has_rbac_permission(codename)
