from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("users:auth-register") if "users" in reverse("auth-register") else "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/login/"
        self.me_url = "/api/v1/auth/me/"

        self.valid_payload = {
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Aziz",
            "last_name": "Karimov",
            "phone_number": "+998901234567",
        }

    def test_user_registration_success(self):
        """Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tadi."""
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "testuser@example.com")
        self.assertEqual(response.data["role"], "user")
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.filter(email="testuser@example.com").exists())

    def test_registration_duplicate_email_fails(self):
        """Mavjud email bilan ro'yxatdan o'tib bo'lmaydi."""
        self.client.post(self.register_url, self.valid_payload)
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_registration_password_mismatch_fails(self):
        """Parollar mos kelmasa ro'yxatdan o'tish rad etiladi."""
        payload = self.valid_payload.copy()
        payload["password_confirm"] = "DifferentPassword123!"
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_role_cannot_be_escalated_via_registration(self):
        """API orqali role='admin' yuborilsa ham foydalanuvchi 'user' bo'lib qoladi."""
        payload = self.valid_payload.copy()
        payload["role"] = "admin"
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "user")

        created_user = User.objects.get(email=payload["email"])
        self.assertEqual(created_user.role, "user")
        self.assertFalse(created_user.is_staff)

    def test_login_and_token_generation(self):
        """To'g'ri ma'lumot bilan login qilib token olinadi."""
        self.client.post(self.register_url, self.valid_payload)
        login_data = {
            "email": self.valid_payload["email"],
            "password": self.valid_payload["password"],
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_me_endpoint_requires_auth(self):
        """Login qilmagan foydalanuvchi /auth/me/ ga kira olmaydi."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_retrieves_and_updates_profile(self):
        """Login qilgan foydalanuvchi o'z profilini ko'ra oladi va tahrirlay oladi."""
        user = User.objects.create_user(
            email="me@example.com",
            password="StrongPassword123!",
            first_name="Initial",
            last_name="Name",
        )
        self.client.force_authenticate(user=user)

        # GET
        get_res = self.client.get(self.me_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data["email"], "me@example.com")

        # PATCH (attempting to change role to admin must not work)
        patch_res = self.client.patch(
            self.me_url,
            {"first_name": "Updated", "role": "admin"},
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["first_name"], "Updated")
        self.assertEqual(patch_res.data["role"], "user")

        user.refresh_from_db()
        self.assertEqual(user.first_name, "Updated")
        self.assertEqual(user.role, "user")
