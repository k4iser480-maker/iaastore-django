import os

from django.apps import AppConfig


class EcositeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecosite'

    def ready(self):
        # Conectar la signal post_save para BackupSettings
        from django.db.models.signals import post_save
        from ecosite.models import BackupSettings
        from ecosite.scheduler import update_schedule

        post_save.connect(update_schedule, sender=BackupSettings)

        # Iniciar el scheduler solo en el proceso principal de runserver
        # (Django ejecuta ready() dos veces por el autoreloader)
        if os.environ.get('RUN_MAIN') == 'true':
            from ecosite.scheduler import start_scheduler
            start_scheduler()
