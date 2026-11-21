from unittest.mock import patch
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.events.models import Event, Registration

User = get_user_model()


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="notif_user@test.com",
            password="UserPass123!",
            role=User.Role.USER,
        )
        self.client.force_authenticate(user=self.user)
        self.now = timezone.now()

    def test_telegram_link_generates_token(self):
        """Telegram bog'lash endpointi havola qaytaradi va token saqlaydi."""
        res = self.client.post("/api/v1/telegram/link/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("link", res.data)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.telegram_link_token)
        self.assertIn(self.user.telegram_link_token, res.data["link"])

    def test_telegram_confirm_with_valid_secret(self):
        """To'g'ri secret bilan Telegram chat_id muvaffaqiyatli bog'lanadi."""
        self.client.post("/api/v1/telegram/link/")
        self.user.refresh_from_db()
        token = self.user.telegram_link_token

        # Unauthenticate to simulate Bot request
        self.client.force_authenticate(user=None)
        secret = getattr(settings, "BOT_API_SECRET", "super-secret-bot-key-2026")
        headers = {"HTTP_X_BOT_SECRET": secret}

        res = self.client.post(
            "/api/v1/telegram/confirm/",
            {"token": token, "chat_id": 987654321},
            **headers,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, 987654321)
        self.assertIsNone(self.user.telegram_link_token)

    def test_telegram_confirm_with_invalid_secret_fails(self):
        """X-Bot-Secret noto'g'ri bo'lsa /telegram/confirm/ rad etadi (403)."""
        self.client.force_authenticate(user=None)
        headers = {"HTTP_X_BOT_SECRET": "wrong-secret"}
        res = self.client.post(
            "/api/v1/telegram/confirm/",
            {"token": "some-token", "chat_id": 12345},
            **headers,
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.notifications.services.send_telegram_message")
    def test_telegram_failure_does_not_break_registration(self, mock_send):
        """Telegram yuborish xatosi bo'lsa ham yozilish muvaffaqiyatli bo'ladi."""
        mock_send.side_effect = Exception("Telegram API timeout")

        event = Event.objects.create(
            title="Resilient Event",
            description="Test",
            event_type=Event.EventType.SEMINAR,
            location="Room 1",
            start_at=self.now + timedelta(days=2),
            end_at=self.now + timedelta(days=2, hours=2),
            capacity=10,
        )

        res = self.client.post(f"/api/v1/events/{event.id}/register/")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Registration.objects.filter(
                user=self.user, event=event, status=Registration.Status.ACTIVE
            ).exists()
        )

    @patch("apps.notifications.services.notify_event_reminder")
    def test_reminder_command_runs_and_marks_reminder_sent(self, mock_reminder):
        """Eslatma bir registration uchun faqat bir marta yuboriladi."""
        self.user.telegram_chat_id = 111222333
        self.user.save()

        # Event starting within 10 hours
        event = Event.objects.create(
            title="Soon Event",
            description="Test",
            event_type=Event.EventType.SEMINAR,
            location="Room 1",
            start_at=self.now + timedelta(hours=10),
            end_at=self.now + timedelta(hours=12),
            status=Event.Status.OPEN,
        )
        reg = Registration.objects.create(
            user=self.user,
            event=event,
            status=Registration.Status.ACTIVE,
            reminder_sent=False,
        )

        # Run command first time
        call_command("send_event_reminders")
        reg.refresh_from_db()
        self.assertTrue(reg.reminder_sent)
        self.assertEqual(mock_reminder.call_count, 1)

        # Run command second time - should not send again
        call_command("send_event_reminders")
        self.assertEqual(mock_reminder.call_count, 1)
