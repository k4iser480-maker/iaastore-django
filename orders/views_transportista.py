from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site

from orders.models import Order, DeliveryStatus
from orders.services.delivery_service import DeliveryService


def _require_transportista(request):
    """Helper: returns transportista or raises HttpResponseForbidden."""
    if not request.user.is_transportista:
        return None
    return request.user.transportista


@login_required(login_url='login')
def dashboard(request):
    transportista = _require_transportista(request)
    if not transportista:
        return HttpResponseForbidden("Acceso denegado: No eres un transportista.")

    # Active orders: all delivery states except Delivered/Completed/Cancelled
    pedidos_activos = Order.objects.filter(
        transportista=transportista,
        status__in=['Assigned', 'Picked Up', 'In Transit', 'Nearby']
    ).select_related('user').order_by('-created_at')

    # For each active order, calculate the next valid action
    for pedido in pedidos_activos:
        pedido.next_status = DeliveryService.get_next_status(pedido)
        pedido.next_status_label = _get_button_label(pedido.next_status)
        pedido.tracking_step = DeliveryService.get_tracking_step(pedido)

    # History: delivered/completed
    pedidos_historial = Order.objects.filter(
        transportista=transportista,
        status__in=['Delivered', 'Completed']
    ).order_by('-fecha_entrega')[:20]

    return render(request, 'transportista/pedidos.html', {
        'pedidos_activos': pedidos_activos,
        'pedidos_historial': pedidos_historial,
    })


@login_required(login_url='login')
def pedido_detail(request, pk):
    transportista = _require_transportista(request)
    if not transportista:
        return HttpResponseForbidden("Acceso denegado.")

    pedido = get_object_or_404(Order, pk=pk)

    if pedido.transportista and pedido.transportista.user != request.user:
        return HttpResponseForbidden("Acceso denegado a este pedido.")

    # Get checkpoints (ascending order by default from model Meta)
    checkpoints = pedido.checkpoints.all()

    # Calculate next action
    next_status = DeliveryService.get_next_status(pedido)
    next_status_label = _get_button_label(next_status)
    tracking_step = DeliveryService.get_tracking_step(pedido)

    # Get city coordinates for map center
    city_coords = DeliveryService.get_city_coordinates(pedido.city)

    return render(request, 'transportista/pedido_detail.html', {
        'pedido': pedido,
        'checkpoints': checkpoints,
        'next_status': next_status,
        'next_status_label': next_status_label,
        'tracking_step': tracking_step,
        'city_lat': city_coords['lat'],
        'city_lng': city_coords['lng'],
    })


@login_required(login_url='login')
def update_delivery_status(request, pk):
    """
    Update delivery status via the transportista's button press.
    Accepts optional GPS coordinates from the browser.
    GPS is NON-BLOCKING: if unavailable, status updates anyway.
    """
    if request.method != 'POST':
        return redirect('transportista:transportista_dashboard')

    transportista = _require_transportista(request)
    if not transportista:
        return HttpResponseForbidden("Acceso denegado.")

    pedido = get_object_or_404(Order, pk=pk)

    if pedido.transportista and pedido.transportista.user != request.user:
        return HttpResponseForbidden("Acceso denegado a este pedido.")

    new_status = request.POST.get('status')
    note = request.POST.get('note', '').strip()

    # GPS coordinates — optional, non-blocking
    latitude = _parse_coordinate(request.POST.get('latitude'))
    longitude = _parse_coordinate(request.POST.get('longitude'))
    accuracy = _parse_float(request.POST.get('accuracy'))

    # Get domain for email links
    current_site = get_current_site(request)

    try:
        DeliveryService.create_checkpoint(
            order=pedido,
            status=new_status,
            user=request.user,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            note=note,
            domain=current_site.domain,
        )
        messages.success(request, f'Estado actualizado: {DeliveryStatus(new_status).label}')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('transportista:transportista_pedido_detail', pk=pk)


def _get_button_label(status):
    """Get the user-friendly button label for a delivery status."""
    LABELS = {
        DeliveryStatus.PICKED_UP:   '📦 Marcar Recogido',
        DeliveryStatus.IN_TRANSIT:  '🚚 Marcar En Camino',
        DeliveryStatus.NEARBY:      '📍 Marcar Cerca del Destino',
        DeliveryStatus.DELIVERED:   '✅ Marcar Entregado',
    }
    return LABELS.get(status, '')


def _parse_coordinate(value):
    """Parse a coordinate string to Decimal, or return None."""
    if not value:
        return None
    try:
        from decimal import Decimal
        return Decimal(value)
    except Exception:
        return None


def _parse_float(value):
    """Parse a float string, or return None."""
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
