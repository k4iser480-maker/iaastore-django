from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account
# Register your models here.

class AccountAdmin(UserAdmin):
    list_display = ('email','first_name','last_name','username','date_joined','last_login','is_active')
    list_display_links = ('email', 'first_name', 'last_name')
    search_fields = ('email','username')
    readonly_fields = ('date_joined','last_login')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    def has_delete_permission(self, request, obj=None):
        return True

admin.site.register(Account, AccountAdmin)