"""
Chatbot Helper — Handlers de flujo de conversación
"""
import re
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail

from store.models import Product
from category.models import Category
from orders.models import Order
from .models import Ticket
from .chatbot_utils import (
    TEXTS, MAIN_MENU_BUTTONS, HOME_BUTTON,
    ORDER_STATUS_MAP, PAYMENT_STATUS_MAP,
    make_response, tokenize,
)


def handle_greeting(message, session):
    """Bienvenida — presenta a Helper y muestra menú principal."""
    session.context = {}
    session.save()
    return make_response(
        [TEXTS['greeting']['welcome'], TEXTS['greeting']['how_can_help']],
        buttons=MAIN_MENU_BUTTONS,
        intent='greeting', confidence=1.0,
    )


def handle_farewell(message, session):
    """Despedida — agradece y limpia contexto."""
    session.context = {}
    session.save()
    return make_response(
        TEXTS['farewell']['bye'],
        buttons=[{"label": "🏠 Nuevo chat", "value": "inicio"}],
        intent='farewell', confidence=1.0,
    )


# ==========================================
# PRODUCTOS Y PRECIOS
# ==========================================

def handle_products(message, session):
    """Maneja búsqueda de productos, detalles y precios."""
    ctx = session.context
    step = ctx.get('step', '')

    # Si viene de un botón de producto específico
    if message.startswith('producto_'):
        try:
            pid = int(message.replace('producto_', ''))
            return _show_product_detail(pid, session)
        except (ValueError, Product.DoesNotExist):
            pass

    # Si viene de un botón de categoría
    if message.startswith('cat_'):
        slug = message.replace('cat_', '')
        return _show_category_products(slug, session)

    # Si el usuario pregunta precio y ya hay un producto en contexto
    if ctx.get('product_id') and step == 'viewing_product':
        tokens = tokenize(message)
        price_words = {'precio', 'cuesta', 'vale', 'costo', 'cuanto'}
        if price_words.intersection(tokens):
            return _show_product_detail(ctx['product_id'], session)

    # Búsqueda por texto libre
    query_tokens = tokenize(message)
    # Eliminar palabras genéricas que no ayudan a la búsqueda
    stop_words = {'busco', 'necesito', 'quiero', 'tienen', 'hay', 'ver',
                  'mostrar', 'producto', 'material', 'precio', 'cuanto',
                  'cuesta', 'vale', 'el', 'la', 'los', 'las', 'un', 'una',
                  'de', 'del', 'para', 'con', 'por', 'que', 'como', 'me',
                  'se', 'es', 'en', 'al', 'su', 'y', 'o', 'a'}
    search_tokens = [t for t in query_tokens if t not in stop_words and len(t) > 2]

    if not search_tokens:
        # No hay query útil — mostrar categorías
        return _show_categories(session)

    # --- Búsqueda inteligente (mismo enfoque que la tienda) ---
    search_phrase = ' '.join(search_tokens)

    # Paso 1: Buscar por frase completa (más preciso)
    products = Product.objects.filter(
        Q(product_name__icontains=search_phrase) |
        Q(description__icontains=search_phrase),
        is_available=True
    )[:6]

    # Paso 2: Si no hay resultados, buscar con AND (todos los tokens deben estar)
    if not products and len(search_tokens) > 1:
        q_filter = Q(is_available=True)
        for token in search_tokens:
            q_filter &= (Q(product_name__icontains=token) | Q(description__icontains=token))
        products = Product.objects.filter(q_filter)[:6]

    # Paso 3: Si aún nada, buscar el token más largo (más específico)
    if not products:
        longest_token = max(search_tokens, key=len)
        products = Product.objects.filter(
            Q(product_name__icontains=longest_token) |
            Q(description__icontains=longest_token),
            is_available=True
        )[:6]

    if not products:
        ctx.update(current_flow='products', step='', fallback_count=0)
        session.context = ctx
        session.save()
        buttons = _get_category_buttons()
        buttons.append(HOME_BUTTON)
        return make_response(
            [TEXTS['products']['no_results'], TEXTS['products']['browse_categories']],
            buttons=buttons,
            intent='products', confidence=0.7,
        )

    # Mostrar resultados
    buttons = []
    for p in products:
        label = f"{p.product_name[:35]} — ${p.price}"
        buttons.append({"label": label, "value": f"producto_{p.id}"})
    buttons.append(HOME_BUTTON)

    ctx.update(current_flow='products', step='showing_results',
               search_query=search_phrase, fallback_count=0)
    session.context = ctx
    session.save()

    return make_response(
        TEXTS['products']['found'].format(count=len(products), query=search_phrase),
        buttons=buttons,
        intent='products', confidence=0.9,
    )


def _show_product_detail(product_id, session):
    """Muestra detalle de un producto específico."""
    try:
        p = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return make_response('No encontré ese producto.', buttons=[HOME_BUTTON])

    stock_text = TEXTS['products']['detail_stock'].format(stock=p.stock) \
        if p.stock > 0 else TEXTS['products']['detail_no_stock']

    lines = [
        f"🏗️ **{p.product_name}**",
        f"💰 Precio: ${p.price}",
    ]
    if p.is_on_sale and p.old_price:
        lines.append(f"🏷️ Antes: ~~${p.old_price}~~ ¡En oferta!")
    lines.append(f"📦 {stock_text}")
    lines.append(f"📂 Categoría: {p.Category.category_name}")
    if p.description:
        lines.append(f"\n{p.description[:200]}")

    detail = '\n'.join(lines)

    buttons = [
        {"label": "🔍 Buscar otro producto", "value": "menu_productos"},
        HOME_BUTTON,
    ]

    ctx = session.context
    ctx.update(current_flow='products', step='viewing_product',
               product_id=product_id, fallback_count=0)
    session.context = ctx
    session.save()

    return make_response(detail, buttons=buttons, intent='products', confidence=1.0)


def _show_categories(session):
    """Muestra las categorías disponibles."""
    buttons = _get_category_buttons()
    buttons.append(HOME_BUTTON)
    ctx = session.context
    ctx.update(current_flow='products', step='browsing_categories', fallback_count=0)
    session.context = ctx
    session.save()
    return make_response(
        ['📂 Estas son nuestras categorías disponibles:',
         '💡 También puedes escribir el nombre de un producto para buscarlo directamente.'],
        buttons=buttons, intent='products', confidence=0.8,
    )


def _show_category_products(slug, session):
    """Muestra productos de una categoría."""
    try:
        cat = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return _show_categories(session)

    products = Product.objects.filter(Category=cat, is_available=True)[:6]
    if not products:
        return make_response(
            f'No hay productos disponibles en {cat.category_name}.',
            buttons=[HOME_BUTTON], intent='products',
        )

    buttons = []
    for p in products:
        buttons.append({"label": f"{p.product_name[:35]} — ${p.price}",
                        "value": f"producto_{p.id}"})
    buttons.append(HOME_BUTTON)

    ctx = session.context
    ctx.update(current_flow='products', step='showing_results', fallback_count=0)
    session.context = ctx
    session.save()

    return make_response(
        f"Productos en **{cat.category_name}**:",
        buttons=buttons, intent='products', confidence=0.9,
    )


def _get_category_buttons():
    cats = Category.objects.all()
    return [{"label": f"📂 {c.category_name}", "value": f"cat_{c.slug}"} for c in cats]


# ==========================================
# PAGOS Y CHECKOUT
# ==========================================

def handle_payments(message, session):
    """Explica métodos de pago disponibles."""
    ctx = session.context
    ctx.update(current_flow='payment', step='', fallback_count=0)
    session.context = ctx
    session.save()

    tokens = tokenize(message)
    # Si pregunta por un método específico
    if 'paypal' in tokens:
        return make_response(TEXTS['payments']['paypal'],
                             buttons=[HOME_BUTTON], intent='payment', confidence=1.0)
    if 'zelle' in tokens:
        return make_response(TEXTS['payments']['zelle'],
                             buttons=[HOME_BUTTON], intent='payment', confidence=1.0)
    if set(tokens) & {'movil', 'pagomovil'}:
        return make_response(TEXTS['payments']['pagomovil'],
                             buttons=[HOME_BUTTON], intent='payment', confidence=1.0)
    if 'cashea' in tokens:
        return make_response(TEXTS['payments']['cashea'],
                             buttons=[HOME_BUTTON], intent='payment', confidence=1.0)

    # Mostrar todos
    msgs = [
        TEXTS['payments']['intro'],
        TEXTS['payments']['paypal'],
        TEXTS['payments']['zelle'],
        TEXTS['payments']['pagomovil'],
        TEXTS['payments']['cashea'],
        TEXTS['payments']['note'],
    ]
    return make_response(msgs, buttons=[HOME_BUTTON], intent='payment', confidence=1.0)


# ==========================================
# NAVEGACIÓN / PROCESO DE COMPRA
# ==========================================

def handle_navigation(message, session):
    """Guía paso a paso del proceso de compra."""
    ctx = session.context
    ctx.update(current_flow='navigation', step='', fallback_count=0)
    session.context = ctx
    session.save()

    buttons = [
        {"label": "🏗️ Ver productos", "value": "menu_productos"},
        HOME_BUTTON,
    ]
    return make_response(TEXTS['navigation']['steps'],
                         buttons=buttons, intent='navigation', confidence=1.0)


# ==========================================
# ENVÍOS
# ==========================================

def handle_shipping(message, session):
    """Información sobre envíos y entregas."""
    ctx = session.context
    ctx.update(current_flow='shipping', step='', fallback_count=0)
    session.context = ctx
    session.save()
    return make_response(TEXTS['shipping']['info'],
                         buttons=[HOME_BUTTON], intent='shipping', confidence=1.0)


# ==========================================
# DASHBOARD / PANEL DE CONTROL
# ==========================================

def handle_dashboard(message, session):
    """Información sobre el panel de control del cliente."""
    ctx = session.context
    ctx.update(current_flow='dashboard', step='', fallback_count=0)
    session.context = ctx
    session.save()
    return make_response(TEXTS['dashboard']['intro'],
                         buttons=[HOME_BUTTON], intent='dashboard', confidence=1.0)


# ==========================================
# PEDIDOS
# ==========================================

def handle_orders(message, session):
    """Consulta de estado de pedidos con validación de privacidad."""
    ctx = session.context
    step = ctx.get('step', '')

    # Paso: verificar email (usuario no autenticado)
    if step == 'verify_email':
        pending_order = ctx.get('pending_order', '')
        try:
            order = Order.objects.get(order_number=pending_order)
        except Order.DoesNotExist:
            ctx.update(step='', pending_order='')
            session.context = ctx
            session.save()
            return make_response(TEXTS['orders']['not_found'], buttons=[HOME_BUTTON],
                                 intent='order_status')

        if message.strip().lower() == order.email.lower():
            ctx.update(step='', pending_order='')
            session.context = ctx
            session.save()
            return _format_order_status(order)
        else:
            ctx.update(step='', pending_order='')
            session.context = ctx
            session.save()
            return make_response(TEXTS['orders']['email_mismatch'],
                                 buttons=[
                                     {"label": "🧑‍💼 Contactar soporte", "value": "menu_soporte"},
                                     HOME_BUTTON
                                 ], intent='order_status')

    # Extraer número de pedido del mensaje
    order_number = _extract_order_number(message)

    if not order_number:
        # Pedir número de pedido
        ctx.update(current_flow='order_status', step='awaiting_order', fallback_count=0)
        session.context = ctx
        session.save()
        return make_response(TEXTS['orders']['ask_number'],
                             buttons=[HOME_BUTTON], intent='order_status', confidence=0.8)

    # Buscar el pedido
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return make_response(TEXTS['orders']['not_found'],
                             buttons=[HOME_BUTTON], intent='order_status')

    # Validación de privacidad
    if session.user:
        if order.user != session.user:
            return make_response(TEXTS['orders']['not_yours'],
                                 buttons=[HOME_BUTTON], intent='order_status')
        return _format_order_status(order)
    else:
        # No autenticado: pedir email
        ctx.update(current_flow='order_status', step='verify_email',
                   pending_order=order_number, fallback_count=0)
        session.context = ctx
        session.save()
        return make_response(
            [TEXTS['orders']['ask_email'], TEXTS['orders']['login_suggestion']],
            buttons=[HOME_BUTTON], intent='order_status',
        )


def _extract_order_number(message):
    """Extrae número de pedido (formato: YYYYMMDD + ID)."""
    match = re.search(r'\b(20\d{6}\d+)\b', message)
    if match:
        return match.group(1)
    # También intentar con solo dígitos largos
    match = re.search(r'\b(\d{9,})\b', message)
    if match:
        return match.group(1)
    return None


def _format_order_status(order):
    """Formatea el estado de un pedido para mostrar al usuario."""
    status_name, status_desc = ORDER_STATUS_MAP.get(
        order.status, (order.status, ''))
    payment_status = PAYMENT_STATUS_MAP.get(
        order.payment_status, order.payment_status)

    lines = [
        f"📋 **Pedido #{order.order_number}**",
        f"👤 {order.full_name()}",
        f"📊 Estado: **{status_name}**",
        f"💳 Pago: {payment_status}",
        f"💰 Total: ${order.order_total:.2f}",
        f"📅 Fecha: {order.created_at.strftime('%d/%m/%Y')}",
        f"\n{status_desc}",
    ]
    return make_response('\n'.join(lines), buttons=[HOME_BUTTON],
                         intent='order_status', confidence=1.0)


# ==========================================
# DEVOLUCIONES
# ==========================================

def handle_returns(message, session):
    """Política de devoluciones."""
    ctx = session.context
    ctx.update(current_flow='returns', step='', fallback_count=0)
    session.context = ctx
    session.save()
    buttons = [
        {"label": "🧑‍💼 Contactar soporte", "value": "menu_soporte"},
        HOME_BUTTON,
    ]
    return make_response(TEXTS['returns']['policy'],
                         buttons=buttons, intent='returns', confidence=1.0)


# ==========================================
# ESCALAMIENTO A SOPORTE
# ==========================================

def handle_support(message, session):
    """Flujo multi-paso para crear ticket de soporte con notificación email."""
    ctx = session.context
    step = ctx.get('step', '')
    collected = ctx.get('collected_data', {})

    if step == 'awaiting_name':
        collected['name'] = message.strip()
        ctx.update(step='awaiting_email', collected_data=collected)
        session.context = ctx
        session.save()
        return make_response(
            TEXTS['support']['ask_email'].format(name=collected['name']),
            intent='support', confidence=1.0,
        )

    elif step == 'awaiting_email':
        collected['email'] = message.strip()
        ctx.update(step='awaiting_order_id', collected_data=collected)
        session.context = ctx
        session.save()
        return make_response(TEXTS['support']['ask_order'],
                             intent='support', confidence=1.0)

    elif step == 'awaiting_order_id':
        order_id = message.strip()
        if order_id.lower() in ('no', 'n', 'ninguno', 'no tengo', '-'):
            order_id = ''
        collected['order_id'] = order_id
        ctx.update(step='awaiting_issue', collected_data=collected)
        session.context = ctx
        session.save()
        return make_response(TEXTS['support']['ask_issue'],
                             intent='support', confidence=1.0)

    elif step == 'awaiting_issue':
        # Crear ticket
        ticket = Ticket.objects.create(
            name=collected.get('name', ''),
            email=collected.get('email', ''),
            order_id=collected.get('order_id', ''),
            issue=message.strip(),
        )
        # Enviar email de notificación
        try:
            send_mail(
                f'[Ticket #{ticket.id}] Nuevo caso de soporte — {collected.get("name", "")}',
                (
                    f'Nombre: {collected.get("name", "")}\n'
                    f'Email: {collected.get("email", "")}\n'
                    f'Pedido: {collected.get("order_id", "N/A")}\n\n'
                    f'Problema:\n{message.strip()}'
                ),
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                fail_silently=True,
            )
        except Exception:
            pass

        # Limpiar contexto
        session.context = {}
        session.save()

        return make_response(
            TEXTS['support']['confirm'].format(
                ticket_id=ticket.id,
                email=collected.get('email', ''),
            ),
            buttons=[{"label": "🏠 Volver al inicio", "value": "inicio"}],
            intent='support', confidence=1.0,
        )

    else:
        # Inicio del flujo de soporte
        ctx.update(current_flow='support', step='awaiting_name',
                   collected_data={}, fallback_count=0)
        session.context = ctx
        session.save()
        return make_response(TEXTS['support']['start'],
                             intent='support', confidence=1.0)


# ==========================================
# FAQ
# ==========================================

def handle_faq(message, session):
    """Muestra la sección de preguntas frecuentes."""
    session.context = {'step': 'faq'}
    session.save()
    messages = [
        TEXTS['faq']['intro'],
        TEXTS['faq']['q1'],
        TEXTS['faq']['q2'],
        TEXTS['faq']['q3']
    ]
    return make_response(
        messages,
        buttons=[HOME_BUTTON],
        intent='faq', confidence=1.0,
    )

# ==========================================
# DASHBOARD
# ==========================================

# ==========================================
# FALLBACK
# ==========================================

def handle_fallback(message, session):
    """Fallback escalonado: 3 niveles progresivos."""
    ctx = session.context
    count = ctx.get('fallback_count', 0)

    if count >= 2:
        # Nivel 3: ofrecer soporte humano
        ctx['fallback_count'] = 0
        session.context = ctx
        session.save()
        return make_response(
            TEXTS['fallback']['level_3'],
            buttons=[
                {"label": "🧑‍💼 Hablar con soporte", "value": "menu_soporte"},
                HOME_BUTTON,
            ],
            intent='fallback', confidence=0.0,
        )
    elif count == 1:
        # Nivel 2
        ctx['fallback_count'] = 2
        session.context = ctx
        session.save()
        return make_response(TEXTS['fallback']['level_2'],
                             buttons=MAIN_MENU_BUTTONS + [HOME_BUTTON],
                             intent='fallback', confidence=0.0)
    else:
        # Nivel 1
        ctx['fallback_count'] = 1
        session.context = ctx
        session.save()
        return make_response(TEXTS['fallback']['level_1'],
                             buttons=MAIN_MENU_BUTTONS,
                             intent='fallback', confidence=0.0)
