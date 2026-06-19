from django.contrib import admin

from ecosite.models import BackupSettings


@admin.register(BackupSettings)
class BackupSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'enabled', 'interval_minutes', 'last_modified')
    readonly_fields = ('last_modified',)
    fieldsets = (
        ('Estado', {
            'fields': ('enabled',),
            'description': 'Active o desactive los respaldos automaticos.',
        }),
        ('Frecuencia', {
            'fields': ('interval_minutes',),
            'description': (
                'Ejemplos: 1 = cada minuto (para pruebas), '
                '60 = cada hora, 1440 = diario, 10080 = semanal.'
            ),
        }),
        ('Informacion', {
            'fields': ('last_modified',),
        }),
    )

    def has_add_permission(self, request):
        # Solo puede existir un registro (singleton)
        if BackupSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuracion
        return False
