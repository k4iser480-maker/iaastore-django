from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.
class MyAccountManager(BaseUserManager):

    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('el usuario debe tener un correo electrónico')
        if not username:
            raise ValueError('el usuario debe tener un nombre de usuario')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, username, email, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

class Permission(models.Model):
    module = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.module} - {self.name}"

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name

class Account(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    roles = models.ManyToManyField(Role, blank=True)
    profile_picture = models.ImageField(upload_to='userprofile/', blank=True, null=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return True

    def has_rbac_permission(self, codename):
        if self.is_superadmin:
            return True
        return self.roles.filter(permissions__codename=codename).exists()

    @property
    def is_transportista(self):
        """Check if user has an associated Transportista profile."""
        return hasattr(self, 'transportista')

    @property
    def creates_sandbox_orders(self):
        """Usuarios internos del sistema. Sus pedidos son sandbox."""
        return self.is_staff or self.is_superadmin


class ActivityLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('TOGGLE', 'Activar/Desactivar'),
        ('STATUS', 'Cambio de Estado'),
    )
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} - {self.action} en {self.module}"

class ShippingAddress(models.Model):
    CITY_CHOICES = (
        ('Barcelona', 'Barcelona'),
        ('Lechería', 'Lechería'),
    )
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='shipping_addresses')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, choices=CITY_CHOICES)
    state = models.CharField(max_length=50, default='Anzoátegui')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Shipping Addresses'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address_line_1}, {self.city}"

class ReferralProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.referral_code}"

class Referral(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('rewarded', 'Recompensado'),
        ('failed', 'Fallido'),
    )
    referrer = models.ForeignKey(Account, related_name='referrals_made', on_delete=models.CASCADE)
    referred = models.OneToOneField(Account, related_name='referred_by', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.referrer.email} invitó a {self.referred.email}"

class AdminChatLog(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='admin_chat_logs')
    question = models.TextField()
    answer = models.TextField()
    intent = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.user.email} - Intent: {self.intent}"