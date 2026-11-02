import os
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser, FarmerProfile, BuyerProfile


class Command(BaseCommand):
    help = 'Seeds initial demonstration accounts for Hackathon evaluation (Farmer, Buyer, Admin) idempotently'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Force reset passwords on existing demo accounts',
        )

    def handle(self, *args, **options):
        seed_enabled = os.getenv('SEED_DEMO_USERS', 'true').lower() in ('true', '1', 't', 'yes')
        if not seed_enabled:
            self.stdout.write(self.style.WARNING('SEED_DEMO_USERS is disabled; skipping demo account seeding.'))
            return

        reset_passwords = options.get('reset_passwords', False)

        # 1. Seed Farmer Demo Account
        farmer_email = "ramesh.farmer@example.com"
        farmer, farmer_created = CustomUser.objects.get_or_create(
            email=farmer_email,
            defaults={
                'phone': '9876543210',
                'full_name': 'Ramesh Kumar Patel',
                'role': CustomUser.Role.FARMER,
                'is_active': True,
            }
        )
        if farmer_created or reset_passwords:
            farmer.set_password("FarmerPassword@123")
            farmer.save()

        f_profile, _ = FarmerProfile.objects.get_or_create(user=farmer)
        if farmer_created:
            f_profile.village = "Pipliya Mandi"
            f_profile.district = "Neemuch"
            f_profile.state = "Madhya Pradesh"
            f_profile.farm_size_acres = 12.50
            f_profile.latitude = 24.4631
            f_profile.longitude = 74.8732
            f_profile.save()

        self.stdout.write(self.style.SUCCESS(
            f"Farmer demo account ready: {farmer_email} (Created: {farmer_created})"
        ))

        # 2. Seed Buyer Demo Account
        buyer_email = "sharma.traders@example.com"
        buyer, buyer_created = CustomUser.objects.get_or_create(
            email=buyer_email,
            defaults={
                'phone': '9123456780',
                'full_name': 'Suresh Sharma',
                'role': CustomUser.Role.BUYER,
                'is_active': True,
            }
        )
        if buyer_created or reset_passwords:
            buyer.set_password("BuyerPassword@123")
            buyer.save()

        b_profile, _ = BuyerProfile.objects.get_or_create(user=buyer)
        if buyer_created:
            b_profile.business_name = "Sharma Agro Commodities Pvt Ltd"
            b_profile.buyer_type = BuyerProfile.BuyerType.WHOLESALER
            b_profile.district = "Indore"
            b_profile.state = "Madhya Pradesh"
            b_profile.gstin = "23ABCDE1234F1Z5"
            b_profile.latitude = 22.7196
            b_profile.longitude = 75.8577
            b_profile.save()

        self.stdout.write(self.style.SUCCESS(
            f"Buyer demo account ready: {buyer_email} (Created: {buyer_created})"
        ))

        # 3. Seed Admin / Superuser Account
        admin_email = "admin@krishisetu.gov.in"
        admin, admin_created = CustomUser.objects.get_or_create(
            email=admin_email,
            defaults={
                'phone': '9999999999',
                'full_name': 'KrishiSetu Admin',
                'role': CustomUser.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if admin_created or reset_passwords:
            admin.set_password("AdminPassword@123")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        self.stdout.write(self.style.SUCCESS(
            f"Admin demo account ready: {admin_email} (Created: {admin_created})"
        ))
