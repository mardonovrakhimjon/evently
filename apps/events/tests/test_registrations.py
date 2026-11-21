from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.events.models import Event, Registration

User = get_user_model()


class RegistrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="attendee@test.com",
            password="AttendeePass123!",
            role=User.Role.USER,
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="OtherPass123!",
            role=User.Role.USER,
        )
        self.client.force_authenticate(user=self.user)

        self.now = timezone.now()
        self.event = Event.objects.create(
            title="Python Clean Code",
            description="Best practices",
            event_type=Event.EventType.SEMINAR,
            location="Room 101",
            start_at=self.now + timedelta(days=3),
            end_at=self.now + timedelta(days=3, hours=2),
            capacity=2,
            status=Event.Status.OPEN,
        )

    def test_user_registers_successfully(self):
        """Foydalanuvchi ochiq tadbirga muvaffaqiyatli yoziladi."""
        res = self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "active")
        self.assertEqual(res.data["event"]["id"], self.event.id)
        self.assertTrue(
            Registration.objects.filter(
                user=self.user, event=self.event, status=Registration.Status.ACTIVE
            ).exists()
        )

    def test_cannot_register_twice(self):
        """Bir tadbirga ikki marta yozilib bo'lmaydi (BR-1)."""
        self.client.post(f"/api/v1/events/{self.event.id}/register/")
        res = self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["code"], "already_registered")

    def test_cannot_register_when_event_is_full(self):
        """Joy qolmagan tadbirga yozilib bo'lmaydi (BR-2)."""
        u1 = User.objects.create_user(email="u1@test.com", password="Pass123!")
        u2 = User.objects.create_user(email="u2@test.com", password="Pass123!")
        Registration.objects.create(user=u1, event=self.event, status=Registration.Status.ACTIVE)
        Registration.objects.create(user=u2, event=self.event, status=Registration.Status.ACTIVE)

        res = self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["code"], "event_full")

    def test_cannot_register_when_event_closed(self):
        """Yopilgan tadbirga yozilib bo'lmaydi (BR-5)."""
        self.event.status = Event.Status.CLOSED
        self.event.save()

        res = self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["code"], "event_closed")

    def test_cannot_register_to_started_event(self):
        """Boshlanib ketgan tadbirga yozilib bo'lmaydi (BR-3)."""
        self.event.start_at = self.now - timedelta(hours=1)
        self.event.save()

        res = self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["code"], "event_started")

    def test_unregister_and_re_register_flow(self):
        """Ro'yxatdan chiqqandan keyin joy bo'shaydi va qayta yozilish mumkin (BR-6)."""
        # Register
        self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(
            self.event.registrations.filter(status=Registration.Status.ACTIVE).count(), 1
        )

        # Unregister
        unreg_res = self.client.post(f"/api/v1/events/{self.event.id}/unregister/")
        self.assertEqual(unreg_res.status_code, status.HTTP_200_OK)
        reg = Registration.objects.get(user=self.user, event=self.event)
        self.assertEqual(reg.status, Registration.Status.CANCELLED)
        self.assertIsNotNone(reg.cancelled_at)

        # Re-register
        rereg_res = self.client.post(f"/api/v1/events/{self.event.id}/register/")
        self.assertEqual(rereg_res.status_code, status.HTTP_201_CREATED)
        reg.refresh_from_db()
        self.assertEqual(reg.status, Registration.Status.ACTIVE)
        self.assertIsNone(reg.cancelled_at)

    def test_cannot_unregister_after_event_started(self):
        """Tadbir boshlangandan keyin undan chiqib bo'lmaydi (BR-6)."""
        Registration.objects.create(
            user=self.user, event=self.event, status=Registration.Status.ACTIVE
        )
        self.event.start_at = self.now - timedelta(minutes=10)
        self.event.save()

        res = self.client.post(f"/api/v1/events/{self.event.id}/unregister/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["code"], "event_started")

    def test_my_registrations_only_shows_own_registrations(self):
        """Foydalanuvchi faqat o'zining ro'yxatdan o'tishlarini ko'radi (BR-10)."""
        Registration.objects.create(
            user=self.user, event=self.event, status=Registration.Status.ACTIVE
        )

        other_event = Event.objects.create(
            title="Other Event",
            description="Other",
            event_type=Event.EventType.SEMINAR,
            location="Room 2",
            start_at=self.now + timedelta(days=5),
            end_at=self.now + timedelta(days=5, hours=2),
        )
        Registration.objects.create(
            user=self.other_user, event=other_event, status=Registration.Status.ACTIVE
        )

        res = self.client.get("/api/v1/me/registrations/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["event"]["id"], self.event.id)
