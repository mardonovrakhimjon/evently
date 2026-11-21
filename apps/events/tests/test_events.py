from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.events.models import Event, Registration

User = get_user_model()


class EventTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="AdminPass123!",
            role=User.Role.ADMIN,
        )
        self.user = User.objects.create_user(
            email="user@test.com",
            password="UserPass123!",
            role=User.Role.USER,
        )
        self.events_url = "/api/v1/events/"

    def test_admin_can_create_event(self):
        """Admin tadbir yarata oladi."""
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        payload = {
            "title": "Django Advanced",
            "description": "Django REST masterclass",
            "event_type": "masterclass",
            "location": "IT Park, Room 301",
            "start_at": (now + timedelta(days=2)).isoformat(),
            "end_at": (now + timedelta(days=2, hours=3)).isoformat(),
            "capacity": 25,
        }
        response = self.client.post(self.events_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Django Advanced")
        self.assertEqual(response.data["available_seats"], 25)
        self.assertEqual(response.data["registered_count"], 0)

    def test_regular_user_cannot_create_event(self):
        """Oddiy foydalanuvchi tadbir yarata olmaydi (403)."""
        self.client.force_authenticate(user=self.user)
        now = timezone.now()
        payload = {
            "title": "Unauthorized Event",
            "description": "Test",
            "event_type": "seminar",
            "location": "Online",
            "start_at": (now + timedelta(days=1)).isoformat(),
            "end_at": (now + timedelta(days=1, hours=2)).isoformat(),
        }
        response = self.client.post(self.events_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_create_event(self):
        """Login qilmagan foydalanuvchi tadbir yarata olmaydi (401)."""
        response = self.client.post(self.events_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_end_at_before_start_at_validation(self):
        """end_at < start_at bo'lsa tadbir yaratilmaydi (BR-7)."""
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        payload = {
            "title": "Invalid Dates",
            "description": "Test",
            "event_type": "seminar",
            "location": "Online",
            "start_at": (now + timedelta(days=2, hours=3)).isoformat(),
            "end_at": (now + timedelta(days=2)).isoformat(),
        }
        response = self.client.post(self.events_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_at", response.data)

    def test_past_date_event_creation_fails(self):
        """O'tgan sanaga yangi tadbir yaratilmaydi (BR-8)."""
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        payload = {
            "title": "Past Event",
            "description": "Test",
            "event_type": "seminar",
            "location": "Online",
            "start_at": (now - timedelta(days=2)).isoformat(),
            "end_at": (now - timedelta(days=2, hours=-2)).isoformat(),
        }
        response = self.client.post(self.events_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_at", response.data)

    def test_cannot_decrease_capacity_below_active_registrations(self):
        """capacity ni faol qatnashuvchilar sonidan kamaytirib bo'lmaydi (BR-9)."""
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        event = Event.objects.create(
            title="Capacity Check",
            description="Test",
            event_type=Event.EventType.SEMINAR,
            location="Room 1",
            start_at=now + timedelta(days=2),
            end_at=now + timedelta(days=2, hours=2),
            capacity=5,
            created_by=self.admin,
        )
        # Create 3 active registrations
        for i in range(3):
            u = User.objects.create_user(email=f"p{i}@test.com", password="Pass123!")
            Registration.objects.create(user=u, event=event, status=Registration.Status.ACTIVE)

        patch_url = f"/api/v1/events/{event.id}/"
        # Attempt to set capacity to 2 (below active count of 3)
        res = self.client.patch(patch_url, {"capacity": 2})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", res.data)

        # Setting capacity to 3 or 4 should succeed
        res_ok = self.client.patch(patch_url, {"capacity": 4})
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data["capacity"], 4)

    def test_admin_can_close_event(self):
        """Admin tadbirni yopa oladi (A6)."""
        self.client.force_authenticate(user=self.admin)
        now = timezone.now()
        event = Event.objects.create(
            title="Open Event",
            description="Test",
            event_type=Event.EventType.SEMINAR,
            location="Room 1",
            start_at=now + timedelta(days=2),
            end_at=now + timedelta(days=2, hours=2),
            status=Event.Status.OPEN,
        )
        res = self.client.post(f"/api/v1/events/{event.id}/close/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CLOSED)

    def test_participants_list_access(self):
        """Faqat admin qatnashuvchilar ro'yxatini ko'ra oladi (A5)."""
        now = timezone.now()
        event = Event.objects.create(
            title="Participants Event",
            description="Test",
            event_type=Event.EventType.SEMINAR,
            location="Room 1",
            start_at=now + timedelta(days=2),
            end_at=now + timedelta(days=2, hours=2),
        )
        Registration.objects.create(user=self.user, event=event, status=Registration.Status.ACTIVE)

        url = f"/api/v1/events/{event.id}/participants/"

        # Regular user receives 403
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

        # Admin receives 200 with participant list
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["email"], self.user.email)
