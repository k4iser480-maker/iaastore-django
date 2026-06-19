from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('manual_payment/', views.manual_payment, name='manual_payment'),
    path('payment_method_instructions/<str:method>/<str:order_number>/', views.payment_method_instructions, name='payment_method_instructions'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('cashea_success/', views.cashea_success, name='cashea_success'),
]