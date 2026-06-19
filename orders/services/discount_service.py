from django.utils import timezone
from orders.models import Coupon, CouponUsage

class DiscountService:
    @staticmethod
    def is_new_user(user):
        """Returns True if the user has 0 completed (paid) orders."""
        if not user or not user.is_authenticated:
            return False
        return user.order_set.filter(payment_status='paid').count() == 0

    @staticmethod
    def apply_coupon(user, cart_total, coupon_code):
        """
        Validates the coupon against user and cart total.
        Returns (is_valid, discount_amount, coupon_obj, message)
        """
        if not coupon_code:
            return False, 0.0, None, "No se proporcionó ningún código."
            
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
        except Coupon.DoesNotExist:
            return False, 0.0, None, "El código ingresado no existe."

        if not coupon.is_active:
            return False, 0.0, None, "Este cupón ya no está activo."

        now = timezone.now()
        if coupon.valid_from and now < coupon.valid_from:
            return False, 0.0, None, "Este cupón aún no es válido."
        if coupon.valid_to and now > coupon.valid_to:
            return False, 0.0, None, "Este cupón ha expirado."

        if coupon.max_uses is not None and coupon.current_uses >= coupon.max_uses:
            return False, 0.0, None, "Este cupón ha alcanzado su límite de usos."

        if cart_total < coupon.min_order_amount:
            return False, 0.0, None, f"El cupón requiere una compra mínima de ${coupon.min_order_amount}."

        if coupon.is_for_new_users_only and not DiscountService.is_new_user(user):
            return False, 0.0, None, "Este cupón es exclusivo para nuevos usuarios en su primera compra."

        # Check if the user already used this specific coupon
        if CouponUsage.objects.filter(user=user, coupon=coupon).exists():
            return False, 0.0, None, "Ya has utilizado este cupón anteriormente."

        discount_amount = (cart_total * coupon.discount_percentage) / 100.0
        return True, discount_amount, coupon, f"¡Cupón aplicado exitosamente! ({coupon.discount_percentage}% de descuento)"

    @staticmethod
    def record_usage(user, coupon, order):
        """Records that a user used a coupon on an order."""
        CouponUsage.objects.create(
            user=user,
            coupon=coupon,
            order=order
        )
        coupon.current_uses += 1
        coupon.save()
