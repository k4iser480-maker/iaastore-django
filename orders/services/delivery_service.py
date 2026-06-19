import logging
from django.db import transaction
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from orders.models import Order, DeliveryCheckpoint, DeliveryStatus

logger = logging.getLogger(__name__)

# ==========================================
# DELIVERY TRANSITIONS (transportista flow)
# ==========================================
# Maps current delivery status → next valid status
# The transportista only sees ONE button: the next valid state.
DELIVERY_TRANSITIONS = {
    DeliveryStatus.PICKED_UP:   DeliveryStatus.IN_TRANSIT,
    DeliveryStatus.IN_TRANSIT:  DeliveryStatus.NEARBY,
    DeliveryStatus.NEARBY:      DeliveryStatus.DELIVERED,
}

# Maps DeliveryStatus → Order.status for syncing
DELIVERY_TO_ORDER_STATUS = {
    DeliveryStatus.PICKED_UP:      'Picked Up',
    DeliveryStatus.IN_TRANSIT:     'In Transit',
    DeliveryStatus.NEARBY:         'Nearby',
    DeliveryStatus.DELIVERED:      'Delivered',
    DeliveryStatus.FAILED_ATTEMPT: 'Failed Attempt',
}

# Statuses that trigger customer email notifications
EMAIL_STATUSES = {
    DeliveryStatus.PICKED_UP,
    DeliveryStatus.IN_TRANSIT,
    DeliveryStatus.NEARBY,
    DeliveryStatus.DELIVERED,
}

# Email subject lines per status
EMAIL_SUBJECTS = {
    DeliveryStatus.PICKED_UP:   'Tu pedido fue recogido',
    DeliveryStatus.IN_TRANSIT:  'Tu pedido está en camino',
    DeliveryStatus.NEARBY:      'Tu pedido llegará pronto',
    DeliveryStatus.DELIVERED:   'Tu pedido ha sido entregado',
}

# Default city coordinates (fallback when GPS unavailable)
CITY_COORDINATES = {
    'Barcelona':      {'lat': 10.1414, 'lng': -64.6861},
    'Lechería':       {'lat': 10.1833, 'lng': -64.6928},
    'Puerto La Cruz': {'lat': 10.2146, 'lng': -64.6297},
}


class DeliveryService:
    """
    Centralized service for all delivery tracking operations.
    Views should ONLY call methods from this class — never manipulate
    checkpoints or delivery status directly.
    """

    @staticmethod
    def get_current_delivery_status(order):
        """Get the latest delivery checkpoint status for an order."""
        latest = order.checkpoints.order_by('-created_at').first()
        return latest.status if latest else None

    @staticmethod
    def get_next_status(order):
        """
        Get the next valid delivery status for the transportista.
        Returns None if no transition is available (terminal state).
        """
        current = DeliveryService.get_current_delivery_status(order)

        # If no checkpoints yet, first action depends on Order.status
        if current is None:
            if order.status == 'Assigned':
                return DeliveryStatus.PICKED_UP
            return None

        return DELIVERY_TRANSITIONS.get(current)

    @staticmethod
    def get_tracking_step(order):
        """
        Calculate the current tracking step number for the progress bar.
        Returns 0-5 (0 = no tracking, 5 = delivered).
        Calculated in backend — templates just use the number.
        """
        STEP_MAP = {
            DeliveryStatus.PICKED_UP: 1,
            DeliveryStatus.IN_TRANSIT: 2,
            DeliveryStatus.NEARBY: 3,
            DeliveryStatus.DELIVERED: 4,
        }
        current = DeliveryService.get_current_delivery_status(order)
        if current is None:
            # Check Order.status for pre-checkpoint states
            if order.status == 'Assigned':
                return 0
            return 0
        return STEP_MAP.get(current, 0)

    @staticmethod
    def get_city_coordinates(city_name):
        """Get default coordinates for a city. Used as fallback."""
        return CITY_COORDINATES.get(city_name, CITY_COORDINATES.get('Barcelona'))

    @staticmethod
    @transaction.atomic
    def create_checkpoint(order, status, user, latitude=None, longitude=None,
                          accuracy=None, note='', domain=None):
        """
        Create a delivery checkpoint and sync Order.status.
        This is the ONLY way to update delivery status.

        Args:
            order: Order instance
            status: DeliveryStatus value (string)
            user: Account who created the checkpoint
            latitude: Optional GPS latitude (Decimal)
            longitude: Optional GPS longitude (Decimal)
            accuracy: Optional GPS accuracy in meters
            note: Optional note (required for failed_attempt)
            domain: Current site domain for email links

        Returns:
            DeliveryCheckpoint instance

        Raises:
            ValueError: If transition is not valid
        """
        # Validate the transition
        current = DeliveryService.get_current_delivery_status(order)

        if status == DeliveryStatus.FAILED_ATTEMPT:
            # Failed attempt is always allowed from any active state
            if current == DeliveryStatus.DELIVERED:
                raise ValueError('No se puede reportar intento fallido en un pedido ya entregado.')
            if not note:
                raise ValueError('Se requiere una nota para reportar un intento fallido.')
        else:
            expected_next = DeliveryService.get_next_status(order)
            if expected_next is None:
                raise ValueError('No hay transiciones disponibles para este pedido.')
            if status != expected_next:
                raise ValueError(
                    f'Transición no válida. Se esperaba "{expected_next}" '
                    f'pero se recibió "{status}".'
                )

        # Create checkpoint
        checkpoint = DeliveryCheckpoint.objects.create(
            order=order,
            status=status,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            note=note,
            created_by=user,
        )

        # Sync Order.status (cache)
        order_status = DELIVERY_TO_ORDER_STATUS.get(status)
        if order_status:
            order.status = order_status

        # Set fecha_entrega on delivery
        if status == DeliveryStatus.DELIVERED:
            order.fecha_entrega = timezone.now()

        order.save()

        # Update transportista availability
        DeliveryService._update_transportista_availability(order, status)

        # Send customer email (non-blocking)
        if status in EMAIL_STATUSES and domain and not order.is_test:
            DeliveryService._send_tracking_email(order, status, domain)

        return checkpoint

    @staticmethod
    def _update_transportista_availability(order, status):
        """Update transportista availability based on delivery status."""
        if not order.transportista:
            return

        t = order.transportista

        if status == DeliveryStatus.DELIVERED:
            # Check if transportista has other active orders
            has_active = Order.objects.filter(
                transportista=t,
                status__in=['Assigned', 'Picked Up', 'In Transit', 'Nearby']
            ).exclude(id=order.id).exists()

            if not has_active:
                t.disponible = True
                t.save()

    @staticmethod
    def _send_tracking_email(order, status, domain):
        """
        Send tracking notification email to the customer.
        Non-blocking: if SMTP fails, log warning but don't break the flow.
        """
        subject = EMAIL_SUBJECTS.get(status)
        if not subject:
            return

        try:
            message = render_to_string('orders/tracking_email.html', {
                'order': order,
                'status': status,
                'status_display': DeliveryStatus(status).label,
                'domain': domain,
            })
            email = EmailMessage(subject, message, to=[order.email])
            email.content_subtype = 'html'
            email.send()
        except Exception as e:
            logger.warning(
                f'Failed to send tracking email for order #{order.order_number}: {e}'
            )
