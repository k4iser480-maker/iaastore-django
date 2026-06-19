import os
import django
import random
import string

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecosite.settings")
django.setup()

from accounts.models import Account, ReferralProfile

def run():
    users_without_profile = Account.objects.filter(referralprofile__isnull=True)
    count = 0
    for user in users_without_profile:
        base_ref_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Ensure unique
        while ReferralProfile.objects.filter(referral_code=base_ref_code).exists():
            base_ref_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
        ReferralProfile.objects.create(user=user, referral_code=base_ref_code)
        count += 1
    
    print(f"Successfully generated {count} referral profiles for existing users.")

if __name__ == '__main__':
    run()
