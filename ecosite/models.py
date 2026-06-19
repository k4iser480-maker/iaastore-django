from django.db import models


class BackupSettings(models.Model):
    """
    Configuracion singleton para la programacion de respaldos automaticos.
    Solo debe existir un registro en la base de datos.
    """
    enabled = models.BooleanField(
        default=True,
        verbose_name='Respaldo activo',
        help_text='Activa o desactiva los respaldos automaticos.',
    )
    interval_minutes = models.PositiveIntegerField(
        default=1440,
        verbose_name='Intervalo (minutos)',
        help_text='Frecuencia del respaldo en minutos. Ejemplos: 1 = cada minuto, 60 = cada hora, 1440 = diario, 10080 = semanal.',
    )
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuracion de Respaldo'
        verbose_name_plural = 'Configuracion de Respaldo'

    def __str__(self):
        estado = 'Activo' if self.enabled else 'Inactivo'
        return f'Respaldo {estado} - cada {self.interval_minutes} min'

    def save(self, *args, **kwargs):
        # Forzar singleton: siempre usar pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Carga o crea la configuracion singleton."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Ticket(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    order_id = models.CharField(max_length=50, blank=True, default='')
    issue = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.order_id}"


class ChatSession(models.Model):
    """Una sesión de chat completa de un usuario con Helper."""
    session_key = models.CharField(max_length=64, db_index=True)
    user = models.ForeignKey(
        'accounts.Account', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='chat_sessions'
    )
    # Estado conversacional estructurado (JSON)
    # Ejemplo: {"current_flow": "products", "step": "showing_results",
    #           "product_id": 42, "fallback_count": 0, "collected_data": {}}
    context = models.JSONField(default=dict, blank=True)
    # Rate limiting: timestamps of recent messages
    message_timestamps = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.user:
            return f"Chat #{self.id} - {self.user.email}"
        return f"Chat #{self.id} - Anónimo ({self.session_key[:8]}...)"


class ChatMessage(models.Model):
    """Cada mensaje individual en una conversación con Helper."""
    SENDER_CHOICES = (
        ('user', 'Usuario'),
        ('bot', 'Helper'),
    )
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.CharField(max_length=4, choices=SENDER_CHOICES)
    text = models.TextField()
    intent_detected = models.CharField(max_length=50, blank=True, default='')
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender}] {self.text[:50]}"
