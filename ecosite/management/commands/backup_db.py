"""
Comando de gestión de Django para respaldar la base de datos SQLite.

Funcionalidades:
- Crea una copia segura de la DB usando la API sqlite3.backup()
- Comprime el respaldo en un archivo ZIP con cifrado AES-256
- Guarda una copia local en la carpeta backups/
- Elimina respaldos locales con más de N días (rotación)
- Envía el respaldo por correo electrónico
- Maneja errores y notifica si el envío falla
- Verifica el tamaño del archivo antes de enviarlo (límite Gmail: 25 MB)
"""

import logging
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pyzipper
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# ── Configuración con valores por defecto ───────────────────────────────────
BACKUP_DIR = getattr(settings, 'BACKUP_DIR', Path(settings.BASE_DIR) / 'backups')
BACKUP_RETENTION_DAYS = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
BACKUP_EMAIL_RECIPIENT = getattr(
    settings, 'BACKUP_EMAIL_RECIPIENT', settings.EMAIL_HOST_USER,
)
BACKUP_ZIP_PASSWORD = getattr(settings, 'BACKUP_ZIP_PASSWORD', '123')
GMAIL_MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024  # 25 MB


class Command(BaseCommand):
    help = 'Crea un respaldo seguro de la base de datos SQLite, lo comprime y lo envía por correo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Solo guarda el respaldo localmente, sin enviarlo por correo.',
        )
        parser.add_argument(
            '--no-cleanup',
            action='store_true',
            help='No elimina respaldos antiguos.',
        )

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'backup_{timestamp}.zip'

        try:
            # 1. Crear directorio de backups si no existe
            backup_dir = Path(BACKUP_DIR)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 2. Realizar la copia segura de la base de datos
            self.stdout.write('[...] Realizando copia segura de la base de datos...')
            db_path = settings.DATABASES['default']['NAME']
            temp_db_path = self._safe_sqlite_backup(db_path)

            # 3. Comprimir con cifrado AES-256
            self.stdout.write('[...] Comprimiendo con cifrado AES-256...')
            zip_path = backup_dir / zip_filename
            self._create_encrypted_zip(temp_db_path, zip_path)

            # Eliminar copia temporal de la DB
            os.remove(temp_db_path)

            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] Respaldo guardado: {zip_path} ({zip_size_mb:.2f} MB)',
                ),
            )

            # 4. Enviar por correo (si no se desactivó)
            if not options['no_email']:
                self._send_backup_email(zip_path, timestamp)

            # 5. Rotación de backups antiguos
            if not options['no_cleanup']:
                self._cleanup_old_backups(backup_dir)

            self.stdout.write(self.style.SUCCESS('[OK] Proceso de respaldo completado exitosamente.'))

        except Exception as exc:
            error_msg = f'[ERROR] Error durante el respaldo: {exc}'
            self.stderr.write(self.style.ERROR(error_msg))
            logger.exception('Error durante el respaldo de la base de datos')
            self._send_error_notification(str(exc))
            raise

    # ── Métodos privados ────────────────────────────────────────────────────

    def _safe_sqlite_backup(self, db_path: str) -> str:
        """
        Usa la API sqlite3.backup() para crear una copia consistente de la DB,
        evitando corrupción por escrituras concurrentes.
        """
        temp_fd, temp_path = tempfile.mkstemp(suffix='.sqlite3')
        os.close(temp_fd)

        source = sqlite3.connect(str(db_path))
        destination = sqlite3.connect(temp_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        return temp_path

    def _create_encrypted_zip(self, db_path: str, zip_path: Path) -> None:
        """
        Crea un archivo ZIP cifrado con AES-256 que contiene la copia de la DB.
        """
        password = BACKUP_ZIP_PASSWORD.encode('utf-8')
        with pyzipper.AESZipFile(
            str(zip_path),
            'w',
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(password)
            # Guardamos la DB dentro del ZIP con un nombre descriptivo
            arcname = f'db_backup_{Path(zip_path).stem.replace("backup_", "")}.sqlite3'
            zf.write(db_path, arcname)

    def _send_backup_email(self, zip_path: Path, timestamp: str) -> None:
        """
        Envía el archivo ZIP como adjunto por correo electrónico.
        Verifica el límite de tamaño de Gmail antes de enviar.
        """
        file_size = zip_path.stat().st_size

        if file_size > GMAIL_MAX_ATTACHMENT_BYTES:
            size_mb = file_size / (1024 * 1024)
            warning = (
                f'[WARN] El archivo de respaldo ({size_mb:.2f} MB) excede el límite '
                f'de Gmail (25 MB). El respaldo se guardó localmente pero NO se '
                f'envio por correo.'
            )
            self.stdout.write(self.style.WARNING(warning))
            logger.warning(warning)
            # Enviar notificación de que no se pudo adjuntar
            self._send_size_warning_email(size_mb, timestamp)
            return

        fecha_formateada = datetime.now().strftime('%d/%m/%Y %H:%M')
        size_mb = file_size / (1024 * 1024)

        subject = f'🗄️ Respaldo DB - IAAStore - {fecha_formateada}'
        body = (
            f'Respaldo automático de la base de datos de IAAStore.\n\n'
            f'📅 Fecha: {fecha_formateada}\n'
            f'📦 Archivo: {zip_path.name}\n'
            f'📏 Tamaño: {size_mb:.2f} MB\n'
            f'🔐 El archivo está protegido con contraseña AES-256.\n\n'
            f'Este es un correo generado automáticamente. '
            f'Para restaurar, descomprima el ZIP con la contraseña configurada '
            f'y reemplace el archivo db.sqlite3 del proyecto.\n'
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=[BACKUP_EMAIL_RECIPIENT],
        )
        email.attach_file(str(zip_path))

        try:
            email.send(fail_silently=False)
            self.stdout.write(
                self.style.SUCCESS(f'[OK] Correo enviado a {BACKUP_EMAIL_RECIPIENT}'),
            )
        except Exception as exc:
            error_msg = f'[WARN] No se pudo enviar el correo: {exc}'
            self.stdout.write(self.style.WARNING(error_msg))
            logger.error(error_msg)
            raise

    def _send_size_warning_email(self, size_mb: float, timestamp: str) -> None:
        """
        Envía un correo de advertencia (sin adjunto) cuando el backup
        excede el límite de Gmail.
        """
        subject = '⚠️ Respaldo DB demasiado grande - IAAStore'
        body = (
            f'El respaldo de la base de datos generado el {timestamp} '
            f'tiene un tamaño de {size_mb:.2f} MB, lo cual excede el límite '
            f'de 25 MB de Gmail.\n\n'
            f'El respaldo fue guardado localmente en el servidor en la '
            f'carpeta backups/, pero NO fue enviado como adjunto.\n\n'
            f'Considere acceder al servidor para descargarlo manualmente.'
        )
        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=[BACKUP_EMAIL_RECIPIENT],
            )
            email.send(fail_silently=True)
        except Exception:
            logger.exception('No se pudo enviar la advertencia de tamaño')

    def _send_error_notification(self, error_message: str) -> None:
        """
        Envía un correo de notificación cuando el proceso de respaldo falla.
        """
        subject = '❌ Error en respaldo DB - IAAStore'
        body = (
            f'Ocurrió un error durante el proceso de respaldo automático '
            f'de la base de datos.\n\n'
            f'Error: {error_message}\n\n'
            f'Por favor, revise los logs del servidor para más detalles.'
        )
        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=[BACKUP_EMAIL_RECIPIENT],
            )
            email.send(fail_silently=True)
        except Exception:
            logger.exception('No se pudo enviar la notificación de error')

    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """
        Elimina archivos de respaldo que tengan más de BACKUP_RETENTION_DAYS días.
        """
        cutoff = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        removed_count = 0

        for backup_file in backup_dir.glob('backup_*.zip'):
            # Extraer la fecha del nombre del archivo (backup_YYYYMMDD_HHMMSS.zip)
            try:
                date_str = backup_file.stem.replace('backup_', '')
                file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                if file_date < cutoff:
                    backup_file.unlink()
                    removed_count += 1
                    self.stdout.write(f'[DEL] Eliminado respaldo antiguo: {backup_file.name}')
            except (ValueError, OSError) as exc:
                logger.warning(f'No se pudo procesar/eliminar {backup_file.name}: {exc}')

        if removed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] Se eliminaron {removed_count} respaldo(s) con mas de '
                    f'{BACKUP_RETENTION_DAYS} dias.',
                ),
            )
        else:
            self.stdout.write('[INFO] No hay respaldos antiguos para eliminar.')
