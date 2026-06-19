import random
import string
from django.utils import timezone
from datetime import timedelta
from accounts.models import Referral
from orders.models import Coupon

class ReferralService:
    @staticmethod
    def generate_unique_code(prefix="REWARD-"):
        """Generates a unique dynamic coupon code."""
        while True:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"{prefix}{suffix}"
            if not Coupon.objects.filter(code=code).exists():
                return code

    @staticmethod
    def reward_referral(order):
        """
        Validates if the user who made the order was referred by someone.
        If they were, and the order meets criteria (>$500), it generates a unique
        coupon for the referrer and marks the referral as rewarded.
        """
        if order.order_total < 500:
            return False, "El pedido no alcanza el mínimo de $500 para recompensa de referido."
            
        if not order.user:
            return False, "El pedido no está asociado a una cuenta registrada."

        try:
            referral = Referral.objects.get(referred=order.user)
        except Referral.DoesNotExist:
            return False, "El usuario no fue referido por nadie."

        if referral.status == 'rewarded':
            return False, "La recompensa de este referido ya fue procesada."

        if order.referral_rewarded:
            return False, "El pedido ya fue marcado como recompensado (protección de doble recompensa)."

        # Generate the dynamic coupon for the referrer
        reward_code = ReferralService.generate_unique_code()
        expiration_date = timezone.now() + timedelta(days=60)

        reward_coupon = Coupon.objects.create(
            code=reward_code,
            discount_percentage=30,
            min_order_amount=500.00,
            is_for_new_users_only=False,
            is_active=True,
            valid_to=expiration_date,
            max_uses=1
        )

        # Update relationships
        referral.status = 'rewarded'
        referral.save()

        order.referral_rewarded = True
        order.save()

        # Ideally here we would also send an email to the referrer with their new code!
        # from store.emails import send_referral_reward_email
        # send_referral_reward_email(referral.referrer, reward_code)

        return True, f"Recompensa generada para {referral.referrer.email}: {reward_code}"
