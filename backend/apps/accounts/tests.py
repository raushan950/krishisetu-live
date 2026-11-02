from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import CustomUser, FarmerProfile, BuyerProfile


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.farmer_register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.token_refresh_url = reverse('auth_token_refresh')
        self.me_url = reverse('auth_current_user')
        self.farmer_profile_url = reverse('farmer_profile')
        self.buyer_profile_url = reverse('buyer_profile')

        self.farmer_data = {
            "email": "ramesh.farmer@example.com",
            "phone": "9876543210",
            "full_name": "Ramesh Kumar",
            "role": "FARMER",
            "password": "FarmerPassword@123",
            "password_confirm": "FarmerPassword@123",
            "village": "Pipliya",
            "district": "Neemuch",
            "state": "Madhya Pradesh",
            "farm_size_acres": "12.50"
        }

        self.buyer_data = {
            "email": "sharma.traders@example.com",
            "phone": "9123456780",
            "full_name": "Suresh Sharma",
            "role": "BUYER",
            "password": "BuyerPassword@123",
            "password_confirm": "BuyerPassword@123",
            "business_name": "Sharma Agro Traders",
            "buyer_type": "WHOLESALER",
            "district": "Indore",
            "state": "Madhya Pradesh",
            "gstin": "23ABCDE1234F1Z5"
        }

    # 1. Registration Tests
    def test_farmer_registration(self):
        """Test successful registration of a farmer and profile generation."""
        response = self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], "ramesh.farmer@example.com")
        self.assertEqual(response.data['user']['role'], "FARMER")
        self.assertIsNotNone(response.data['user']['farmer_profile'])
        self.assertIsNone(response.data['user']['buyer_profile'])
        self.assertIsNotNone(response.data['user']['profile'])
        self.assertEqual(response.data['user']['profile']['district'], "Neemuch")

        # Verify database record
        user = CustomUser.objects.get(email="ramesh.farmer@example.com")
        self.assertTrue(hasattr(user, 'farmer_profile'))
        self.assertEqual(user.farmer_profile.district, "Neemuch")
        self.assertEqual(str(user.farmer_profile.farm_size_acres), "12.50")

    def test_buyer_registration(self):
        """Test successful registration of a buyer and profile generation."""
        response = self.client.post(self.farmer_register_url, self.buyer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], "BUYER")
        self.assertIsNotNone(response.data['user']['buyer_profile'])
        self.assertIsNone(response.data['user']['farmer_profile'])
        self.assertIsNotNone(response.data['user']['profile'])
        self.assertEqual(response.data['user']['profile']['business_name'], "Sharma Agro Traders")

        # Verify database record
        user = CustomUser.objects.get(email="sharma.traders@example.com")
        self.assertTrue(hasattr(user, 'buyer_profile'))
        self.assertEqual(user.buyer_profile.business_name, "Sharma Agro Traders")

    def test_registration_duplicate_email(self):
        """Test that registering with an existing email returns 400 Bad Request."""
        self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        duplicate_data = self.farmer_data.copy()
        duplicate_data['phone'] = "9000000001"
        response = self.client.post(self.farmer_register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_duplicate_phone(self):
        """Test that registering with an existing phone returns 400 Bad Request."""
        self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        duplicate_data = self.farmer_data.copy()
        duplicate_data['email'] = "different.email@example.com"
        response = self.client.post(self.farmer_register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response.data)

    def test_registration_password_mismatch(self):
        """Test that mismatched passwords return 400 Bad Request."""
        invalid_data = self.farmer_data.copy()
        invalid_data['password_confirm'] = "Mismatch@123"
        response = self.client.post(self.farmer_register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_registration_invalid_role(self):
        """Test that invalid role or ADMIN registration via public endpoint is rejected."""
        invalid_data = self.farmer_data.copy()
        invalid_data['role'] = "ADMIN"
        response = self.client.post(self.farmer_register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)

    def test_registration_weak_password(self):
        """Test that common or entirely numeric passwords fail validation."""
        weak_data = self.farmer_data.copy()
        weak_data['password'] = "123456"
        weak_data['password_confirm'] = "123456"
        response = self.client.post(self.farmer_register_url, weak_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_invalid_phone(self):
        invalid_data = self.farmer_data.copy()
        invalid_data['phone'] = '98-123'
        response = self.client.post(self.farmer_register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response.data)

    def test_registration_missing_required_fields(self):
        """Test that missing mandatory fields (full_name, phone, email) return 400."""
        incomplete_data = {
            "email": "incomplete@example.com",
            "password": "SomePassword@123",
            "password_confirm": "SomePassword@123",
            "role": "FARMER"
        }
        response = self.client.post(self.farmer_register_url, incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', response.data)
        self.assertIn('full_name', response.data)

    # 2. Login Tests
    def test_farmer_login_and_unified_jwt_payload(self):
        """Test user login returns access/refresh tokens and unified user payload."""
        self.client.post(self.farmer_register_url, self.farmer_data, format='json')

        login_payload = {
            "email": "  Ramesh.Farmer@Example.com  ",  # tests casing & whitespace normalization
            "password": "FarmerPassword@123"
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], "FARMER")
        # Verify unified schema has both explicit and generic profile keys
        self.assertIsNotNone(response.data['user']['farmer_profile'])
        self.assertIsNone(response.data['user']['buyer_profile'])
        self.assertIsNotNone(response.data['user']['profile'])
        self.assertEqual(response.data['user']['profile']['district'], "Neemuch")

    def test_buyer_login_and_unified_jwt_payload(self):
        """Test buyer login returns unified payload with buyer_profile."""
        self.client.post(self.farmer_register_url, self.buyer_data, format='json')

        login_payload = {
            "email": "sharma.traders@example.com",
            "password": "BuyerPassword@123"
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], "BUYER")
        self.assertIsNotNone(response.data['user']['buyer_profile'])
        self.assertIsNone(response.data['user']['farmer_profile'])
        self.assertIsNotNone(response.data['user']['profile'])
        self.assertEqual(response.data['user']['profile']['business_name'], "Sharma Agro Traders")

    def test_login_invalid_password(self):
        """Test login with incorrect password returns 401."""
        self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        response = self.client.post(self.login_url, {
            "email": "ramesh.farmer@example.com",
            "password": "WrongPassword@999"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email(self):
        """Test login with non-existent email returns 401."""
        response = self.client.post(self.login_url, {
            "email": "nobody@example.com",
            "password": "AnyPassword@123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        """Test that inactive users cannot log in."""
        self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        user = CustomUser.objects.get(email="ramesh.farmer@example.com")
        user.is_active = False
        user.save()

        response = self.client.post(self.login_url, {
            "email": "ramesh.farmer@example.com",
            "password": "FarmerPassword@123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test refreshing access token using refresh token."""
        reg_response = self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        refresh_token = reg_response.data['tokens']['refresh']

        response = self.client.post(self.token_refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    # 3. Profile & /auth/me/ Tests
    def test_current_user_me_farmer(self):
        """Test authenticated GET /api/v1/auth/me/ for farmer."""
        reg_response = self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        access_token = reg_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "ramesh.farmer@example.com")
        self.assertIsNotNone(response.data['farmer_profile'])
        self.assertIsNone(response.data['buyer_profile'])
        self.assertIsNotNone(response.data['profile'])
        self.assertEqual(response.data['farmer_profile']['village'], "Pipliya")

    def test_current_user_me_buyer(self):
        """Test authenticated GET /api/v1/auth/me/ for buyer."""
        reg_response = self.client.post(self.farmer_register_url, self.buyer_data, format='json')
        access_token = reg_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "sharma.traders@example.com")
        self.assertIsNotNone(response.data['buyer_profile'])
        self.assertIsNone(response.data['farmer_profile'])
        self.assertIsNotNone(response.data['profile'])

    def test_current_user_me_admin(self):
        """Test authenticated GET /api/v1/auth/me/ for admin does not fabricate farmer/buyer profile."""
        admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            phone="9999999991",
            full_name="Admin Test",
            password="AdminPassword@123"
        )
        login_res = self.client.post(self.login_url, {
            "email": "admin@example.com",
            "password": "AdminPassword@123"
        }, format='json')
        admin_token = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], "ADMIN")
        self.assertIsNone(response.data['farmer_profile'])
        self.assertIsNone(response.data['buyer_profile'])
        self.assertIsNone(response.data['profile'])

    # 4. Role-based Permission Enforcement
    def test_unauthenticated_requests_are_rejected(self):
        """Test unauthenticated access to protected endpoints returns 401."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_role_based_permission_enforcement(self):
        """Test that farmers cannot access buyer profile endpoints and vice-versa."""
        farmer_reg = self.client.post(self.farmer_register_url, self.farmer_data, format='json')
        farmer_token = farmer_reg.data['access']

        buyer_reg = self.client.post(self.farmer_register_url, self.buyer_data, format='json')
        buyer_token = buyer_reg.data['access']

        # Farmer accessing farmer profile -> 200 OK
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {farmer_token}')
        response = self.client.get(self.farmer_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Farmer accessing buyer profile -> 403 FORBIDDEN
        response = self.client.get(self.buyer_profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Buyer accessing buyer profile -> 200 OK
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {buyer_token}')
        response = self.client.get(self.buyer_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Buyer accessing farmer profile -> 403 FORBIDDEN
        response = self.client.get(self.farmer_profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class HealthCheckTests(APITestCase):
    def test_health_check_confirms_database_connectivity(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_frontend_origin_is_allowed_for_options_preflight(self):
        response = self.client.options(
            reverse('auth_login'),
            HTTP_ORIGIN='https://instant-geode-9y9nkbl.tmp.now',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,authorization',
        )
        self.assertEqual(
            response['Access-Control-Allow-Origin'],
            'https://instant-geode-9y9nkbl.tmp.now',
        )

    def test_vercel_preview_origin_is_allowed(self):
        response = self.client.options(
            reverse('auth_login'),
            HTTP_ORIGIN='https://instant-geode-9y9nkbl-raushan-kumars-projects-fed41dec.vercel.app',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,authorization',
        )
        self.assertEqual(
            response['Access-Control-Allow-Origin'],
            'https://instant-geode-9y9nkbl-raushan-kumars-projects-fed41dec.vercel.app',
        )
