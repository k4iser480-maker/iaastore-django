from django.contrib import admin
from .models import Payment, Order, OrderProduct, Transportista

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'payment_id', 'payment_method', 'amount_paid', 'status', 'created_at', 'receipt']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'full_name', 'email', 'city', 'phone', 'order_total', 'tax', 'status', 'payment_status', 'created_at']
    list_filter = ['is_delivery', 'transportista', 'status', 'payment_status']
    search_fields = ['order_number', 'first_name', 'last_name', 'email', 'phone']
    list_per_page = 20
    inlines = [OrderProductInline]

    def save_model(self, request, obj, form, change):
        if change:
            old_transportista = None if not obj.pk else Order.objects.get(pk=obj.pk).transportista
            
            if old_transportista is None and obj.transportista is not None:
                obj.status = 'en_camino'
                transportista = obj.transportista
                transportista.disponible = False
                transportista.save()

                # Enviar email
                from django.template.loader import render_to_string
                from django.core.mail import EmailMessage
                from django.contrib.sites.shortcuts import get_current_site
                current_site = get_current_site(request)
                
                mail_subject = 'Nuevo pedido asignado'
                message = render_to_string('orders/transportista_email.html', {
                    'transportista': transportista,
                    'order': obj,
                    'domain': current_site.domain,
                })
                try:
                    send_email = EmailMessage(mail_subject, message, to=[transportista.email])
                    send_email.send()
                except Exception as e:
                    pass # Evitar que falle guardar si hay error de correo

        super().save_model(request, obj, form, change)

class OrderProductAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'product', 'quantity', 'product_price', 'ordered']

class TransportistaAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'disponible']
    list_filter = ['disponible']

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(Transportista, TransportistaAdmin)
