from django.db import models
from accounts.models import Account
from store.models import Product


class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    receipt = models.FileField(upload_to='receipts/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.payment_id
    
class Transportista(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    email_notificaciones = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=15)
    vehiculo = models.CharField(max_length=50, blank=True, null=True)
    disponible = models.BooleanField(default=True)

    @property
    def email(self):
        return self.email_notificaciones or self.user.email

    def __str__(self):
        return self.user.full_name()

from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    min_order_amount = models.FloatField(default=500.00)
    is_for_new_users_only = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)
    current_uses = models.IntegerField(default=0)
    
    def __str__(self):
        return self.code

class CouponUsage(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"

class OrderQuerySet(models.QuerySet):
    def real(self):
        return self.filter(is_test=False)

    def sandbox(self):
        return self.filter(is_test=True)

class Order(models.Model):
    objects = OrderQuerySet.as_manager()

    PAYMENT_STATUS = (
        ('pending', 'Pendiente de Pago'),
        ('review', 'En Revisión'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
    )
    STATUS = (
        ('New', 'Nuevo'),
        ('Processing', 'Procesando'),
        ('Assigned', 'Asignado'),
        ('Picked Up', 'Recogido'),
        ('In Transit', 'En Camino'),
        ('Nearby', 'Cerca del Destino'),
        ('Delivered', 'Entregado'),
        ('Completed', 'Completado'),
        ('Cancelled', 'Cancelado'),
        ('Failed Attempt', 'Intento Fallido'),
    )
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    igtf_tax = models.FloatField(default=0.0)
    payment_fee = models.FloatField(default=0.0)
    shipping_cost = models.FloatField(default=0.0)
    is_delivery = models.BooleanField(default=True)
    shipping_address = models.ForeignKey('accounts.ShippingAddress', on_delete=models.SET_NULL, null=True, blank=True)
    transportista = models.ForeignKey(Transportista, on_delete=models.SET_NULL, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    status = models.CharField(max_length=20, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    is_exception = models.BooleanField(default=False)
    exception_reason = models.TextField(null=True, blank=True)
    is_test = models.BooleanField(default=False)
    
    # Discount and Referrals
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.FloatField(default=0.0)
    referral_rewarded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def full_address(self):
        return f'{self.address_line_1}, {self.address_line_2}'

    @property
    def is_real(self):
        return not self.is_test

    def __str__(self):
        return self.first_name

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name


# ==========================================
# DELIVERY TRACKING
# ==========================================
class DeliveryStatus(models.TextChoices):
    PICKED_UP = 'picked_up', 'Recogido por Transportista'
    IN_TRANSIT = 'in_transit', 'En Camino'
    NEARBY = 'nearby', 'Cerca del Destino'
    DELIVERED = 'delivered', 'Entregado'
    FAILED_ATTEMPT = 'failed_attempt', 'Intento de Entrega Fallido'


class DeliveryCheckpoint(models.Model):
    """
    Source of truth for delivery history.
    Order.status is just a cached/synced version of the latest checkpoint.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='checkpoints')
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Checkpoint {self.get_status_display()} - Pedido #{self.order.order_number}'