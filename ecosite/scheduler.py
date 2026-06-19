"""
Planificador de respaldos automaticos usando APScheduler.

Inicia un BackgroundScheduler que ejecuta el comando backup_db
segun la configuracion almacenada en BackupSettings.

Protecciones:
- max_instances=1: evita ejecuciones simultaneas si un respaldo tarda mas que el intervalo.
- coalesce=True: si se acumulan ejecuciones perdidas, solo ejecuta una.
- Solo se inicia una vez (guarda via _scheduler_started).
"""

import logging
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

logger = logging.getLogger(__name__)

JOB_ID = 'backup_db_job'

_scheduler = None
_scheduler_started = False


def _run_backup():
    """Funcion que ejecuta el comando de respaldo."""
    try:
        logger.info('[Scheduler] Ejecutando respaldo automatico...')
        call_command('backup_db')
        logger.info('[Scheduler] Respaldo automatico completado.')
    except Exception:
        logger.exception('[Scheduler] Error durante el respaldo automatico.')


def _deferred_start():
    """
    Logica real de inicio del scheduler, ejecutada tras un breve delay
    para evitar acceder a la DB durante AppConfig.ready().
    """
    global _scheduler, _scheduler_started

    from ecosite.models import BackupSettings

    _scheduler = BackgroundScheduler()

    try:
        config = BackupSettings.load()
    except Exception:
        logger.warning('[Scheduler] No se pudo cargar BackupSettings. Usando valores por defecto.')
        config = None

    if config and config.enabled:
        interval = config.interval_minutes
        _scheduler.add_job(
            _run_backup,
            trigger='interval',
            minutes=interval,
            id=JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        logger.info(f'[Scheduler] Respaldo programado cada {interval} minuto(s).')
    elif config and not config.enabled:
        logger.info('[Scheduler] Respaldos automaticos desactivados.')
    else:
        _scheduler.add_job(
            _run_backup,
            trigger='interval',
            minutes=1440,
            id=JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        logger.info('[Scheduler] Respaldo programado con intervalo por defecto (1440 min).')

    _scheduler.start()
    _scheduler_started = True
    logger.info('[Scheduler] Planificador iniciado.')


def start_scheduler():
    """
    Programa el inicio del scheduler con un delay de 2 segundos
    para evitar acceder a la base de datos durante ready().
    Solo se ejecuta una vez por proceso.
    """
    global _scheduler_started

    if _scheduler_started:
        return

    # Marcar como iniciado para evitar doble inicio
    _scheduler_started = True
    # Diferir el acceso a la DB 2 segundos
    timer = threading.Timer(2.0, _deferred_start)
    timer.daemon = True
    timer.start()


def update_schedule(sender, instance, **kwargs):
    """
    Signal handler para post_save de BackupSettings.
    Actualiza el job del scheduler dinamicamente cuando se modifica
    la configuracion desde el panel de administracion.
    """
    global _scheduler

    if _scheduler is None or not _scheduler_started:
        return

    # Remover el job existente si lo hay
    try:
        _scheduler.remove_job(JOB_ID)
    except Exception:
        pass

    if instance.enabled:
        interval = instance.interval_minutes
        _scheduler.add_job(
            _run_backup,
            trigger='interval',
            minutes=interval,
            id=JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        logger.info(
            f'[Scheduler] Intervalo actualizado a {interval} minuto(s).'
        )
    else:
        logger.info('[Scheduler] Respaldos automaticos desactivados desde el admin.')
