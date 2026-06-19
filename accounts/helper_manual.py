# -*- coding: utf-8 -*-
"""
Helper Manual — Contenido del chatbot Helper organizado por módulos.

Cada módulo tiene:
  - title: Nombre visible del módulo
  - roles: lista de roles que pueden ver este módulo
             'all'          → cualquier usuario autenticado
             'staff'        → is_staff (admins y superadmins, NO transportistas)
             'superadmin'   → is_superadmin solamente
             'transportista' → is_transportista solamente
  - sections: dict {id_semántico: {label, content, keywords}}
  - keywords: palabras clave para búsqueda libre a nivel de módulo
"""

MODULES = {
    # ──────────────────────────────────────────────
    # MÓDULO DE CLIENTES
    # ──────────────────────────────────────────────
    'clientes': {
        'title': '🛒 Módulo de Clientes',
        'roles': ['staff', 'superadmin'],
        'keywords': ['cliente', 'clientes', 'compra', 'comprar', 'tienda', 'catalogo'],
        'sections': {
            'client_catalogo': {
                'label': '🔍 Exploración y Catálogo',
                'keywords': ['catalogo', 'buscar', 'producto', 'productos', 'busqueda', 'filtro', 'categorias', 'deseos', 'wishlist', 'resena', 'reseña'],
                'content': (
                    "**Exploración y Catálogo**\n\n"
                    "En la página principal, los clientes pueden usar la barra de búsqueda o el filtro de categorías "
                    "en el menú lateral para encontrar productos. También disponen de filtros de precio (mínimo y máximo).\n\n"
                    "Al hacer clic en un producto, acceden a su detalle, donde pueden ver imágenes, descripciones, "
                    "stock disponible y leer reseñas de otros compradores.\n\n"
                    "Si un producto les interesa para más adelante, pueden usar el icono de corazón para agregarlo "
                    "a su **Lista de Deseos** personal."
                ),
            },
            'client_carrito': {
                'label': '🛒 Carrito de Compras',
                'keywords': ['carrito', 'agregar', 'cantidad', 'cupon', 'descuento', 'envio', 'moneda', 'bolivares', 'dolares', 'tasa'],
                'content': (
                    "**Carrito de Compras**\n\n"
                    "Al hacer clic en \"Agregar al Carrito\", el producto se guarda temporalmente. "
                    "En la página del carrito, el cliente puede:\n\n"
                    "- Ajustar las cantidades (con los botones + y -).\n"
                    "- Aplicar códigos de cupones de descuento.\n"
                    "- Visualizar un estimado automático del costo de envío, calculado en base al peso de los productos y la dirección.\n"
                    "- Alternar la moneda visualizada (Dólares USD o Bolívares VES) según la tasa de cambio oficial."
                ),
            },
            'client_chatbot': {
                'label': '🤖 Asistente Virtual (Helper)',
                'keywords': ['chatbot', 'asistente', 'helper', 'bot', 'ayuda', 'consulta'],
                'content': (
                    "**Asistente Virtual (Chatbot Helper)**\n\n"
                    "En cualquier momento, el cliente puede interactuar con el chatbot asistente inteligente llamado "
                    "\"Helper\", integrado en la tienda.\n\n"
                    "Este responderá consultas, dudas comunes o le ayudará en su navegación por la plataforma."
                ),
            },
            'client_checkout': {
                'label': '💳 Proceso de Compra (Checkout)',
                'keywords': ['checkout', 'pago', 'pagar', 'paypal', 'igtf', 'iva', 'impuesto', 'comision', 'pasarela', 'zelle', 'movil', 'cashea'],
                'content': (
                    "**Proceso de Compra (Checkout)**\n\n"
                    "Una vez listo, el cliente procede al pago:\n\n"
                    "1. Seleccionar o agregar una dirección de envío completa.\n"
                    "2. Seleccionar el método de pago:\n"
                    "   - **PayPal (automático):** el sistema suma IGTF (3%) y comisiones de la pasarela.\n"
                    "   - **Zelle, Pago Móvil o Cashea (manual):** se aplica IVA (16%) o IGTF (3%) según corresponda, "
                    "y se muestran las instrucciones bancarias."
                ),
            },
            'client_comprobante': {
                'label': '🧾 Confirmación de Pago Manual',
                'keywords': ['comprobante', 'recibo', 'subir', 'transferencia', 'revision', 'manual'],
                'content': (
                    "**Confirmación de Pago Manual**\n\n"
                    "Para métodos manuales (Zelle, Pago Móvil, Cashea), el cliente debe:\n\n"
                    "1. Realizar la transferencia bancaria.\n"
                    "2. Subir una foto o archivo PDF del recibo (comprobante) en el formulario de la página.\n"
                    "3. Al enviar el comprobante, el pedido queda en estado **\"En Revisión\"**.\n"
                    "4. El cliente recibe un correo electrónico automático con el número de orden y la factura."
                ),
            },
            'client_seguimiento': {
                'label': '📦 Seguimiento de Pedidos',
                'keywords': ['seguimiento', 'rastreo', 'tracking', 'trazabilidad', 'checkpoint', 'geolocalizacion', 'confirmar', 'recepcion'],
                'content': (
                    "**Seguimiento de Pedidos**\n\n"
                    "Desde su panel de control, el cliente puede ver el estatus de su compra.\n\n"
                    "Cuando el transportista esté en ruta, el cliente visualizará un registro de trazabilidad "
                    "en tiempo real (checkpoints geolocalizados).\n\n"
                    "Una vez recibido el paquete, el cliente cuenta con un botón para **confirmar la recepción exitosa**."
                ),
            },
        },
    },

    # ──────────────────────────────────────────────
    # MÓDULO DE TRANSPORTISTAS
    # ──────────────────────────────────────────────
    'transportistas': {
        'title': '🚚 Módulo de Transportistas',
        'roles': ['transportista', 'superadmin'],
        'keywords': ['transportista', 'transportistas', 'entrega', 'entregas', 'ruta', 'conductor', 'delivery'],
        'sections': {
            'carrier_pedidos': {
                'label': '📋 Panel de Pedidos',
                'keywords': ['pedidos', 'panel', 'asignados', 'pendientes'],
                'content': (
                    "**Panel de Pedidos del Transportista**\n\n"
                    "Acceda a la ruta de \"Pedidos\" en su panel. Identifique las filas con pedidos asignados, "
                    "organizados desde los más recientes.\n\n"
                    "Haga clic en el botón de detalles de un pedido para acceder a la información de entrega: "
                    "dirección del cliente, número de teléfono (con acceso rápido para llamar) y nota del pedido."
                ),
            },
            'carrier_estados': {
                'label': '🔄 Actualización de Estado Logístico',
                'keywords': ['estado', 'logistico', 'recogido', 'camino', 'cerca', 'entregado', 'actualizar', 'marcar'],
                'content': (
                    "**Actualización de Estado Logístico**\n\n"
                    "A medida que avanza la entrega, actualice el progreso usando los botones intuitivos:\n\n"
                    "1. **\"Marcar Recogido\"** → al salir del almacén.\n"
                    "2. **\"Marcar En Camino\"** → durante la ruta.\n"
                    "3. **\"Marcar Cerca del Destino\"** → al aproximarse.\n"
                    "4. **\"Marcar Entregado\"** → al entregar el paquete."
                ),
            },
            'carrier_gps': {
                'label': '📍 Registro GPS y Notas',
                'keywords': ['gps', 'coordenadas', 'ubicacion', 'nota', 'notas', 'geolocalizacion'],
                'content': (
                    "**Registro GPS y Notas**\n\n"
                    "**Importante:** En cada cambio de estado, el sistema solicitará capturar opcionalmente "
                    "las coordenadas GPS actuales del navegador y le permitirá agregar una nota "
                    "(ej. \"Entregado al conserje\").\n\n"
                    "Estos datos se guardan como puntos de control que tanto el cliente como el administrador pueden ver."
                ),
            },
            'carrier_historial': {
                'label': '📜 Historial de Entregas',
                'keywords': ['historial', 'completadas', 'anteriores'],
                'content': (
                    "**Historial de Entregas**\n\n"
                    "El transportista tiene acceso a una pestaña de historial con sus últimas entregas completadas exitosamente."
                ),
            },
        },
    },

    # ──────────────────────────────────────────────
    # MÓDULO DE ADMINISTRACIÓN
    # ──────────────────────────────────────────────
    'admin': {
        'title': '⚙️ Módulo de Administración',
        'roles': ['staff', 'superadmin'],
        'keywords': ['admin', 'administracion', 'backoffice', 'panel', 'gestion'],
        'sections': {
            'admin_pedidos': {
                'label': '📑 Gestión de Pedidos',
                'keywords': ['pedidos', 'ordenes', 'aprobar', 'validar', 'comprobante', 'estado', 'procesando', 'pago', 'manual', 'revision'],
                'content': (
                    "**Gestión de Pedidos**\n\n"
                    "En la sección de \"Pedidos\", el administrador verá todas las órdenes.\n\n"
                    "Para órdenes con pagos manuales (Zelle, Pago Móvil, Cashea) en estado \"En Revisión\":\n"
                    "1. Abrir los detalles del pedido.\n"
                    "2. Descargar o visualizar el comprobante subido por el cliente.\n"
                    "3. Verificar la transacción en el banco.\n"
                    "4. Hacer clic en **\"Aprobar Pago\"** → el pedido pasa a \"Procesando\".\n\n"
                    "También se pueden forzar transiciones de estado para correcciones operativas."
                ),
            },
            'admin_inventario': {
                'label': '📦 Gestión de Productos e Inventario',
                'keywords': ['inventario', 'productos', 'crear', 'stock', 'excel', 'importar', 'exportar', 'peso', 'dimensiones'],
                'content': (
                    "**Gestión de Productos e Inventario**\n\n"
                    "En \"Productos\", se visualiza el catálogo completo. El administrador puede:\n\n"
                    "- **Crear** productos nuevos ingresando nombre, categoría, dimensiones físicas "
                    "(Largo, Ancho, Alto y Peso) para el cálculo de fletes, y su precio.\n"
                    "- **Activar/Desactivar** productos sin borrarlos.\n"
                    "- **Exportar** → descarga todo el inventario filtrado en un archivo Excel.\n"
                    "- **Importar** → sube un archivo Excel para actualizar precios, stock o crear productos masivamente."
                ),
            },
            'admin_transportistas': {
                'label': '🚛 Gestión de Transportistas',
                'keywords': ['transportistas', 'conductor', 'vehiculo', 'asignar', 'notificar'],
                'content': (
                    "**Gestión de Transportistas**\n\n"
                    "Se permite designar a cualquier usuario registrado como Transportista, ingresando sus datos "
                    "de vehículo y teléfono.\n\n"
                    "Desde la vista de órdenes, el administrador asigna los transportistas disponibles a los pedidos "
                    "que ya estén \"Procesando\", notificándoles automáticamente por correo."
                ),
            },
            'admin_roles': {
                'label': '🔐 Roles y Usuarios',
                'keywords': ['roles', 'rbac', 'usuarios', 'permisos', 'bloquear', 'eliminar', 'staff'],
                'content': (
                    "**Roles y Usuarios (RBAC)**\n\n"
                    "Basado en el sistema RBAC, permite:\n\n"
                    "- **Crear Roles** específicos (ej. Gestor de Inventario) seleccionando en una matriz "
                    "a qué módulos tienen acceso.\n"
                    "- Asignar estos roles a los usuarios de tipo \"Staff\".\n"
                    "- **Bloquear** y **Eliminar** usuarios."
                ),
            },
            'admin_backups': {
                'label': '💾 Gestión de Respaldos (Backups)',
                'keywords': ['backup', 'respaldo', 'respaldos', 'restaurar', 'json', 'programar', 'automatico'],
                'content': (
                    "**Gestión de Respaldos (Backups)**\n\n"
                    "El administrador puede proteger la plataforma ingresando a \"Respaldos\":\n\n"
                    "- Crear respaldos **Completos** o **Parciales** (seleccionando módulos específicos).\n"
                    "- Esto genera un archivo JSON seguro.\n"
                    "- Se puede **descargar**, **subir**, **eliminar** o **restaurar** la base de datos.\n"
                    "- Incluye una herramienta para **programar respaldos automáticos** cada cierto intervalo de minutos."
                ),
            },
            'admin_logs': {
                'label': '📊 Registro de Actividad (Logs)',
                'keywords': ['logs', 'actividad', 'auditoria', 'registro', 'historial'],
                'content': (
                    "**Registro de Actividad (Logs)**\n\n"
                    "Los Super Administradores tienen acceso a un reporte inmodificable donde se audita toda acción "
                    "realizada en el panel (ej. quién aprobó un pago, quién borró un usuario), junto a su fecha exacta."
                ),
            },
            'admin_chatbot': {
                'label': '💬 Chatbot Asistente Interno',
                'keywords': ['helper', 'chat', 'asistente', 'interno'],
                'content': (
                    "**Chatbot Asistente Interno (Helper)**\n\n"
                    "El administrador cuenta con un asistente de chat exclusivo en el panel de administración "
                    "que le ayuda a obtener resúmenes rápidos de ventas y soporte."
                ),
            },
        },
    },

    # ──────────────────────────────────────────────
    # PREGUNTAS FRECUENTES (FAQ)
    # ──────────────────────────────────────────────
    'faq': {
        'title': '❓ Preguntas Frecuentes',
        'roles': ['all'],
        'keywords': ['faq', 'problema', 'error', 'ayuda', 'solucion', 'frecuente', 'frecuentes'],
        'sections': {
            'faq_login': {
                'label': '🔑 No puedo entrar al sistema',
                'keywords': ['entrar', 'login', 'sesion', 'clave', 'contrasena', 'activacion', 'verificar', 'acceso'],
                'content': (
                    "**No puedo entrar al sistema**\n\n"
                    "**Causa probable:** Usuario/Clave erróneos o cuenta sin verificar.\n\n"
                    "**Solución:** Verifique que las mayúsculas no estén activas. "
                    "Revise su correo (incluyendo Spam) para encontrar el enlace de activación. "
                    "Utilice el enlace de recuperación de contraseña en la pantalla de inicio."
                ),
            },
            'faq_comprobante': {
                'label': '📎 El comprobante de pago no se guarda',
                'keywords': ['comprobante', 'guardar', 'archivo', 'formato', 'invalido', 'subir'],
                'content': (
                    "**El comprobante de pago no se guarda**\n\n"
                    "**Causa probable:** Falta un campo obligatorio o el archivo tiene un formato inválido.\n\n"
                    "**Solución:** Asegúrese de subir una imagen válida (JPG, PNG) o PDF del recibo "
                    "y complete todos los campos bancarios requeridos en el proceso de compra."
                ),
            },
            'faq_gps': {
                'label': '📍 El transportista no actualiza el mapa con GPS',
                'keywords': ['gps', 'mapa', 'ubicacion', 'permisos', 'navegador', 'desactivado'],
                'content': (
                    "**El transportista no actualiza el mapa con GPS**\n\n"
                    "**Causa probable:** GPS desactivado o bloqueo de permisos en su navegador móvil.\n\n"
                    "**Solución:** El transportista debe otorgar explícitamente los permisos de \"Ubicación\" "
                    "al navegador web de su teléfono para que la geolocalización quede vinculada al estado."
                ),
            },
            'faq_server_error': {
                'label': '🔴 Error \"Server Error (500)\" al respaldar',
                'keywords': ['500', 'server', 'error', 'respaldar', 'restaurar', 'fallo'],
                'content': (
                    "**Error \"Server Error (500)\" al respaldar o restaurar**\n\n"
                    "**Causa probable:** Fallo temporal de escritura o base de datos.\n\n"
                    "**Solución:** Espere unos minutos y vuelva a intentar. "
                    "Si persiste, notifique al equipo de soporte y verifique los registros del servidor."
                ),
            },
            'faq_estado_pedido': {
                'label': '⏳ El pedido no cambia de estado tras enviarse',
                'keywords': ['pedido', 'estado', 'revision', 'cambiar', 'aprobado'],
                'content': (
                    "**El pedido no cambia de estado tras enviarse**\n\n"
                    "**Causa probable:** Aún no ha sido validado administrativamente.\n\n"
                    "**Solución:** Recuerde que tras subir el recibo de pago manual, la orden queda \"En Revisión\". "
                    "Se debe esperar a que el Administrador apruebe la transacción."
                ),
            },
        },
    },
}


def get_all_searchable_entries():
    """
    Returns a flat list of dicts for free-text search:
    [{ 'module_id', 'section_id', 'keywords', 'content', 'label' }, ...]
    """
    entries = []
    for mod_id, mod_data in MODULES.items():
        for sec_id, sec_data in mod_data['sections'].items():
            entries.append({
                'module_id': mod_id,
                'section_id': sec_id,
                'label': sec_data['label'],
                'keywords': mod_data.get('keywords', []) + sec_data.get('keywords', []),
                'content': sec_data['content'],
                'roles': mod_data['roles'],
            })
    return entries
