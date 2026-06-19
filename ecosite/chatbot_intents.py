"""
Chatbot Helper — Detector de intenciones por scoring
"""
from .chatbot_utils import normalize, tokenize


class IntentDetector:
    """Detecta la intención del mensaje usando scoring ponderado por tokens."""

    # Keywords con peso: high=3, medium=2, low=1
    INTENT_KEYWORDS = {
        'greeting': {
            'high': ['hola', 'buenos dias', 'buenas tardes', 'buenas noches',
                     'hey', 'saludos'],
            'medium': ['que tal', 'como estas'],
        },
        'products': {
            'high': ['producto', 'productos', 'material', 'materiales',
                     'hierro', 'acero', 'aislante', 'aislantes',
                     'refractario', 'refractarios', 'ladrillo', 'ladrillos',
                     'lamina', 'laminas', 'perfil', 'perfiles', 'barra',
                     'barras', 'catalogo', 'fibra', 'manta', 'mortero'],
            'medium': ['busco', 'necesito', 'tienen', 'disponible',
                       'disponibilidad', 'stock', 'hay'],
            'low': ['ver', 'mostrar', 'quiero'],
        },
        'prices': {
            'high': ['precio', 'precios', 'cuanto cuesta', 'cuanto vale',
                     'costo', 'costos', 'tarifa', 'cotizacion', 'cotizar'],
            'medium': ['oferta', 'ofertas', 'descuento', 'promocion',
                       'barato', 'economico', 'rebaja'],
        },
        'payment': {
            'high': ['pago', 'pagar', 'zelle', 'paypal', 'pago movil',
                     'cashea', 'transferencia', 'metodo de pago',
                     'metodos de pago', 'forma de pago'],
            'medium': ['tarjeta', 'factura', 'comision', 'iva', 'impuesto',
                       'igtf'],
        },
        'checkout': {
            'high': ['checkout', 'finalizar compra', 'proceso de compra',
                     'como compro', 'como comprar'],
            'medium': ['carrito', 'comprar', 'proceso', 'paso a paso',
                       'pasos'],
        },
        'order_status': {
            'high': ['pedido', 'orden', 'estado del pedido', 'seguimiento',
                     'tracking', 'donde esta mi pedido', 'mi pedido',
                     'numero de pedido', 'consultar pedido'],
            'medium': ['enviado', 'entregado', 'llego'],
        },
        'shipping': {
            'high': ['envio', 'envios', 'delivery', 'despacho', 'flete',
                     'costo de envio', 'envio gratis'],
            'medium': ['entregar', 'entrega', 'direccion', 'zona',
                       'barcelona', 'lecheria', 'recoger', 'retiro'],
        },
        'cancellation': {
            'high': ['cancelar', 'cancelacion', 'anular', 'anular pedido'],
        },
        'returns': {
            'high': ['devolucion', 'devoluciones', 'devolver', 'cambio',
                     'cambiar', 'reembolso'],
            'medium': ['garantia', 'danado', 'defectuoso', 'roto'],
        },
        'support': {
            'high': ['soporte', 'ayuda humana', 'agente', 'hablar con alguien',
                     'reclamo', 'queja', 'problema grave', 'representante',
                     'atencion al cliente', 'ticket'],
            'medium': ['no funciona', 'error', 'problema', 'falla'],
        },
        'dashboard': {
            'high': ['dashboard', 'panel', 'panel de control', 'perfil', 'mi cuenta',
                     'configuracion', 'mis datos', 'direcciones'],
            'medium': ['informacion', 'resumen'],
        },
        'farewell': {
            'high': ['gracias', 'adios', 'chao', 'hasta luego', 'bye',
                     'nos vemos', 'listo', 'perfecto gracias'],
            'medium': ['ok gracias', 'vale', 'genial'],
        },
        'faq': {
            'high': ['faq', 'preguntas frecuentes', 'problema frecuente',
                     'no puedo entrar', 'no se guarda', 'no cambia de estado', 'comprobante de pago'],
            'medium': ['preguntas', 'problemas', 'frecuentes', 'solucion de problemas', 'error 500'],
        },
    }

    def detect(self, message, context=None):
        """
        Retorna lista de (intent, score) ordenada por score desc.
        Usa contexto previo como desempate.
        """
        tokens = tokenize(message)
        msg_normalized = normalize(message)
        scores = {}

        for intent, levels in self.INTENT_KEYWORDS.items():
            score = 0

            # Match por tokens completos (evita falsos positivos)
            for keyword in levels.get('high', []):
                kw_tokens = keyword.split()
                if len(kw_tokens) > 1:
                    # Multi-word: buscar en texto completo
                    if keyword in msg_normalized:
                        score += 3
                else:
                    # Single word: buscar en tokens
                    if keyword in tokens:
                        score += 3

            for keyword in levels.get('medium', []):
                kw_tokens = keyword.split()
                if len(kw_tokens) > 1:
                    if keyword in msg_normalized:
                        score += 2
                else:
                    if keyword in tokens:
                        score += 2

            for keyword in levels.get('low', []):
                if keyword in tokens:
                    score += 1

            # Bonus de contexto: si el flow actual coincide, desempate
            if context and context.get('current_flow') == intent and score > 0:
                score += 1

            if score > 0:
                scores[intent] = score

        # Merge: prices se fusiona con products
        if 'prices' in scores:
            if 'products' in scores:
                scores['products'] = max(scores['products'], scores['prices']) + 1
            else:
                scores['products'] = scores['prices']
            del scores['prices']

        # Merge: checkout se fusiona con navigation
        if 'checkout' in scores and 'payment' not in scores:
            scores['navigation'] = scores.pop('checkout')

        # Merge: shipping info
        if 'shipping' in scores and 'order_status' in scores:
            # Si ambos, priorizar order_status si tiene más score
            if scores['order_status'] >= scores['shipping']:
                del scores['shipping']
            else:
                del scores['order_status']

        sorted_intents = sorted(scores.items(), key=lambda x: -x[1])
        return sorted_intents
