"""
Chatbot Helper — Motor principal de conversación

Orden de procesamiento:
1. Detectar botones (producto_, inicio, cat_, menu_*)
2. Ver si hay step activo → continuar flujo
3. Detectar intents por scoring
4. Fallback
"""
from datetime import timedelta
from django.utils import timezone

from .chatbot_intents import IntentDetector
from .chatbot_utils import TEXTS, MAIN_MENU_BUTTONS, make_response
from .chatbot_handlers import (
    handle_greeting, handle_farewell, handle_products,
    handle_payments, handle_navigation, handle_shipping,
    handle_orders, handle_returns, handle_support, handle_fallback,
    handle_dashboard, _show_categories, handle_faq,
)

# Timeout de sesión: 30 minutos sin interacción → reset
SESSION_TIMEOUT_MINUTES = 30


class ChatEngine:
    def __init__(self):
        self.detector = IntentDetector()

    def process(self, message, session):
        """Procesa un mensaje y retorna respuesta JSON."""

        # --- 0. Expiración de sesión ---
        if session.updated_at < timezone.now() - timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            session.context = {}
            session.save()

        # --- 0b. Fusión anón → user (ya hecho en view) ---

        ctx = session.context

        # --- 1. Detectar comandos de botón directamente (sin NLP) ---
        button_response = self._handle_button_command(message, session)
        if button_response:
            return button_response

        # --- 2. Si hay step activo, continuar flujo ---
        if ctx.get('step'):
            flow = ctx.get('current_flow', '')
            return self._continue_flow(message, session, flow)

        # --- 3. Detectar intents ---
        intents = self.detector.detect(message, ctx)

        if not intents or intents[0][1] < 2:
            # Score muy bajo → fallback
            return handle_fallback(message, session)

        top_intent, top_score = intents[0]

        # Reset fallback count al detectar intención válida
        if ctx.get('fallback_count', 0) > 0:
            ctx['fallback_count'] = 0
            session.context = ctx
            session.save()

        # --- 4. Enrutar al handler ---
        return self._route(top_intent, message, session, top_score)

    def _handle_button_command(self, message, session):
        """Detecta valores de botón y enruta directamente."""
        msg = message.strip().lower()

        # Botón de inicio → reset total
        if msg == 'inicio':
            session.context = {}
            session.save()
            return make_response(
                [TEXTS['greeting']['welcome_back'],
                 TEXTS['greeting']['how_can_help']],
                buttons=MAIN_MENU_BUTTONS,
                intent='greeting', confidence=1.0,
            )

        # Botón de productos → mostrar categorías directamente
        if msg == 'menu_productos':
            fc = session.context.get('fallback_count', 0)
            session.context = {'current_flow': 'products', 'fallback_count': fc}
            session.save()
            return _show_categories(session)

        # Otros botones de menú principal
        menu_map = {
            'menu_pagos': ('payment', handle_payments),
            'menu_pedidos': ('order_status', handle_orders),
            'menu_soporte': ('support', handle_support),
            'menu_dashboard': ('dashboard', handle_dashboard),
            'menu_faq': ('faq', handle_faq),
        }

        if msg in menu_map:
            flow_name, handler = menu_map[msg]
            fc = session.context.get('fallback_count', 0)
            session.context = {'current_flow': flow_name, 'fallback_count': fc}
            session.save()
            return handler(message, session)

        # Botones de producto (producto_123)
        if msg.startswith('producto_'):
            return handle_products(message, session)

        # Botones de categoría (cat_acero)
        if msg.startswith('cat_'):
            return handle_products(message, session)

        return None  # No es un comando de botón

    def _continue_flow(self, message, session, flow):
        """Continúa un flujo activo según el step actual."""
        flow_handlers = {
            'products': handle_products,
            'payment': handle_payments,
            'order_status': handle_orders,
            'support': handle_support,
            'dashboard': handle_dashboard,
        }

        handler = flow_handlers.get(flow)
        if handler:
            return handler(message, session)

        # Flow desconocido → fallback
        return handle_fallback(message, session)

    def _route(self, intent, message, session, score):
        """Enruta al handler correcto según la intención detectada."""
        handlers = {
            'greeting': handle_greeting,
            'products': handle_products,
            'payment': handle_payments,
            'navigation': handle_navigation,
            'shipping': handle_shipping,
            'order_status': handle_orders,
            'cancellation': handle_orders,
            'returns': handle_returns,
            'support': handle_support,
            'dashboard': handle_dashboard,
            'farewell': handle_farewell,
            'faq': handle_faq,
        }

        handler = handlers.get(intent, handle_fallback)
        return handler(message, session)
