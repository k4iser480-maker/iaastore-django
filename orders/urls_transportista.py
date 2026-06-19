from django.urls import path
from . import views_transportista

app_name = 'transportista'

urlpatterns = [
    path('pedidos/', views_transportista.dashboard, name='transportista_dashboard'),
    path('pedido/<int:pk>/', views_transportista.pedido_detail, name='transportista_pedido_detail'),
    path('pedido/<int:pk>/actualizar-estado/', views_transportista.update_delivery_status, name='transportista_update_status'),
    # Keep old URL for backwards compatibility
    path('pedido/<int:pk>/completar/', views_transportista.update_delivery_status, name='transportista_completar_pedido'),
]
