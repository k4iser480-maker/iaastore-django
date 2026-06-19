"""
Chatbot Helper — Utilidades y textos externalizados
"""
import re
import unicodedata


# ==========================================
# NORMALIZACIÓN DE TEXTO
# ==========================================

def normalize(text):
    """Normaliza texto: lower, sin tildes, sin puntuación."""
    text = text.lower().strip()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def tokenize(text):
    """Divide texto normalizado en tokens."""
    return normalize(text).split()


# ==========================================
# RESPUESTAS ESTÁNDAR
# ==========================================

def make_response(messages, buttons=None, intent='', confidence=0.0):
    """Construye respuesta JSON estándar."""
    msg_list = []
    if isinstance(messages, str):
        messages = [messages]
    for m in messages:
        msg_list.append({'text': m, 'type': 'bot'})
    result = {'messages': msg_list, 'intent': intent, 'confidence': confidence}
    if buttons:
        result['buttons'] = buttons
    return result


# ==========================================
# BOTONES PRINCIPALES
# ==========================================

MAIN_MENU_BUTTONS = [
    {"label": "🏗️ Productos y Precios", "value": "menu_productos"},
    {"label": "💳 Pagos y Checkout", "value": "menu_pagos"},
    {"label": "📦 Mis Pedidos", "value": "menu_pedidos"},
    {"label": "🖥️ Mi Dashboard", "value": "menu_dashboard"},
    {"label": "🧑‍💼 Soporte Humano", "value": "menu_soporte"},
    {"label": "❓ Preguntas Frecuentes", "value": "menu_faq"},
]

HOME_BUTTON = {"label": "🏠 Volver al inicio", "value": "inicio"}


# ==========================================
# TEXTOS EXTERNALIZADOS
# ==========================================

TEXTS = {
    'greeting': {
        'welcome': '¡Hola! Soy Helper 🤖, tu asistente de IAA Store.',
        'how_can_help': '¿En qué puedo ayudarte hoy?',
        'welcome_back': '¡Hola de nuevo! ¿En qué más puedo ayudarte?',
    },
    'faq': {
        'intro': '❓ **Preguntas Frecuentes (FAQ)**\n\nAquí tienes la solución a los problemas más comunes:',
        'q1': '🔐 **No puedo entrar al sistema**\n*Causa:* Usuario/Clave erróneos o cuenta sin verificar.\n*Solución:* Verifique que las mayúsculas no estén activas. Revise su correo (incluyendo Spam) para el enlace de activación o utilice recuperar contraseña.',
        'q2': '🧾 **El comprobante de pago no se guarda**\n*Causa:* Falta un campo o archivo inválido.\n*Solución:* Asegúrese de subir una imagen (JPG, PNG) o PDF y complete todos los campos bancarios requeridos.',
        'q3': '⏳ **El pedido no cambia de estado tras enviarse**\n*Causa:* Aún no ha sido validado administrativamente.\n*Solución:* Tras subir el recibo, la orden queda "En Revisión". Debe esperar a que el Administrador apruebe la transacción.',
    },
    'dashboard': {
        'intro': (
            '🖥️ **Tu Panel de Control (Dashboard)**\n\n'
            'Al iniciar sesión, tendrás acceso a tu panel personal donde puedes:\n\n'
            '📦 **Pedidos Recientes:** Ver el historial y resumen de tus compras.\n'
            '🚚 **Estado Logístico:** Seguir la trazabilidad en tiempo real de tus envíos.\n'
            '⚙️ **Configuración:** Actualizar tu perfil y contraseña.\n'
            '📍 **Direcciones:** Administrar tu lista de direcciones de envío.'
        ),
    },
    'fallback': {
        'level_1': 'No estoy seguro de haber entendido 🤔\n¿Podrías elegir una de estas opciones?',
        'level_2': 'Hmm, no logro entenderte. Intenta con palabras más simples o elige una opción:',
        'level_3': 'Parece que no logro entender tu consulta. ¿Te gustaría hablar con un agente de soporte?',
    },
    'products': {
        'ask_search': '¿Qué material o producto estás buscando?',
        'no_results': 'No encontré productos con ese nombre. ¿Podrías intentar con otro término?',
        'found': 'Encontré {count} resultado(s) para "{query}":',
        'detail_stock': '✅ Disponible ({stock} en stock)',
        'detail_no_stock': '❌ Agotado',
        'browse_categories': 'También puedes explorar por categoría:',
    },
    'payments': {
        'intro': 'Estos son los métodos de pago disponibles en IAA Store:',
        'paypal': '💳 **PayPal**: Pago automático y seguro. Se aplica comisión de 5.4% + $0.30 y un IGTF del 3%.',
        'zelle': '🏦 **Zelle (USD)**: Transferencia a Banesco USA.\n• Titular: Industrias de Aislantes y Acero, I.A.A.\n• Email: zelle@iaacaven.com\n• Se aplica IGTF del 3%.',
        'pagomovil': '📱 **Pago Móvil**: Banco Banesco (0134).\n• RIF: J-12345678\n• Teléfono: 0414-1234567\n• Se aplica IVA del 16%.',
        'cashea': '🛒 **Cashea**: Compra ahora, paga después.\n• Abre la app Cashea\n• Busca "IAA Store"\n• Se aplica IVA del 16%.',
        'note': '📝 El total final siempre se muestra antes de confirmar la compra.',
    },
    'navigation': {
        'steps': (
            '🛒 **Proceso de compra paso a paso:**\n\n'
            '1️⃣ Navega por categorías o busca productos\n'
            '2️⃣ Agrega los materiales al carrito\n'
            '3️⃣ Revisa tu carrito (cantidades y productos)\n'
            '4️⃣ Completa tus datos de envío\n'
            '5️⃣ Selecciona el método de pago\n'
            '6️⃣ Confirma la compra\n\n'
            '💡 El IVA y las comisiones se calculan automáticamente según el método de pago elegido.'
        ),
    },
    'orders': {
        'ask_number': '¿Cuál es tu número de pedido? Lo encuentras en el email de confirmación.',
        'not_found': 'No encontré un pedido con ese número. Verifica que esté bien escrito.',
        'not_yours': 'No puedo mostrarte información de este pedido. Asegúrate de estar usando la cuenta correcta.',
        'ask_email': 'Para proteger tu información, necesito verificar tu identidad.\n¿Cuál es el email que usaste al hacer el pedido?',
        'email_mismatch': 'El email no coincide con el del pedido. Por seguridad, no puedo mostrar la información.\nSi crees que es un error, contacta a soporte.',
        'login_suggestion': 'Para consultar pedidos más fácilmente, te recomiendo iniciar sesión.',
    },
    'returns': {
        'policy': (
            '📦 **Política de Devoluciones:**\n\n'
            '• Plazo: 7 días continuos desde la recepción\n'
            '• El producto debe estar en estado original, sin uso\n'
            '• Algunos materiales a medida no admiten devolución\n\n'
            '📧 Para solicitar una devolución, contacta a soporte:\n'
            '• Email: info@iaacaven.com\n'
            '• WhatsApp: 0424-882-4015'
        ),
    },
    'support': {
        'start': 'Entiendo, voy a ayudarte a crear un ticket de soporte.\nPara comenzar, ¿cuál es tu nombre?',
        'ask_email': 'Gracias, {name}. ¿Y tu correo electrónico?',
        'ask_order': '¿Tienes un número de pedido relacionado? Si no, escribe "no".',
        'ask_issue': '¿Podrías describir brevemente tu problema o consulta?',
        'confirm': (
            '✅ Tu ticket de soporte ha sido creado (#{ticket_id}).\n\n'
            'Un agente revisará tu caso y te contactará al correo {email}.\n\n'
            'También puedes contactarnos directamente:\n'
            '📧 info@iaacaven.com\n'
            '📞 0424-882-4015'
        ),
    },
    'farewell': {
        'bye': '¡Gracias por contactarnos! Si necesitas algo más, aquí estaré. ¡Hasta pronto! 👋',
    },
    'shipping': {
        'info': (
            '🚚 **Información de envíos:**\n\n'
            '• Realizamos envíos a Barcelona y Lechería\n'
            '• **¡Envío GRATIS en pedidos mayores a $500!**\n'
            '• El costo se calcula automáticamente en checkout\n'
            '• También puedes recoger en tienda sin costo\n\n'
            '📍 Dirección: Av. Fuerzas Armadas, Centro Industrial, Barcelona'
        ),
    },
}

# Status translations for orders
ORDER_STATUS_MAP = {
    'New': ('Nuevo', 'Tu pedido fue recibido y está siendo procesado.'),
    'Processing': ('Procesando', 'Estamos preparando tu pedido.'),
    'Assigned': ('Asignado', 'Tu pedido ya tiene un transportista asignado.'),
    'In Transit': ('En Camino', 'Tu pedido está en ruta hacia ti.'),
    'Delivered': ('Entregado', 'Tu pedido fue entregado exitosamente.'),
    'Completed': ('Completado', 'Tu pedido está completado.'),
    'Cancelled': ('Cancelado', 'Este pedido fue cancelado.'),
}

PAYMENT_STATUS_MAP = {
    'pending': 'Pendiente de pago',
    'review': 'En revisión',
    'paid': 'Pagado',
    'failed': 'Fallido',
}
