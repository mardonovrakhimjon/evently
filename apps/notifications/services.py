import logging
import httpx
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def send_telegram_message(chat_id: int, text: str) -> bool:
    """Send message via Telegram Bot API sendMessage endpoint."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token or bot_token == "dummy_telegram_bot_token":
        logger.info(f"Telegram bot token not configured. Message skipped for chat {chat_id}: {text}")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                return True
            logger.warning(
                f"Telegram sendMessage failed for chat {chat_id}: {response.status_code} {response.text}"
            )
            return False
    except Exception as exc:
        logger.error(f"Error sending Telegram message to {chat_id}: {exc}")
        return False


def notify_registration(registration_id: int) -> None:
    """
    T1: Notify user and admins about a new successful registration.
    Called inside transaction.on_commit or background.
    """
    from apps.events.models import Registration

    try:
        registration = (
            Registration.objects.select_related("user", "event")
            .filter(id=registration_id, status=Registration.Status.ACTIVE)
            .first()
        )
        if not registration:
            return

        user = registration.user
        event = registration.event

        # 1. Notify the user if linked with telegram
        if user.telegram_chat_id:
            formatted_date = event.start_at.strftime("%d-%B, %H:%M")
            user_msg = (
                f"✅ <b>Siz tadbirga muvaffaqiyatli yozildingiz!</b>\n\n"
                f"📌 <b>{event.title}</b>\n"
                f"🗓 {formatted_date}\n"
                f"📍 {event.location}"
            )
            send_telegram_message(user.telegram_chat_id, user_msg)

        # 2. Notify all admins who linked their telegram
        admin_users = User.objects.filter(
            role=User.Role.ADMIN,
            telegram_chat_id__isnull=False,
        )
        if admin_users.exists():
            active_count = event.registrations.filter(
                status=Registration.Status.ACTIVE
            ).count()
            capacity_str = str(event.capacity) if event.capacity is not None else "∞"
            user_contact = (
                f"{user.full_name} ({user.phone_number})"
                if user.phone_number
                else user.full_name
            )
            admin_msg = (
                f"🆕 <b>Yangi qatnashuvchi</b>\n\n"
                f"👤 {user_contact}\n"
                f"📌 {event.title}\n"
                f"👥 Band joylar: {active_count} / {capacity_str}"
            )
            for admin_user in admin_users:
                send_telegram_message(admin_user.telegram_chat_id, admin_msg)
    except Exception as exc:
        logger.error(f"Error in notify_registration({registration_id}): {exc}")


def notify_event_reminder(registration_id: int) -> bool:
    """
    T2: Send event reminder to user.
    """
    from apps.events.models import Registration

    try:
        registration = (
            Registration.objects.select_related("user", "event")
            .filter(id=registration_id, status=Registration.Status.ACTIVE)
            .first()
        )
        if not registration or not registration.user.telegram_chat_id:
            return False

        event = registration.event
        formatted_date = event.start_at.strftime("%d-%B, %H:%M")
        reminder_msg = (
            f"⏰ <b>Eslatma!</b>\n\n"
            f"Ertaga siz yozilgan tadbir bo‘lib o‘tadi:\n"
            f"📌 <b>{event.title}</b>\n"
            f"🗓 {formatted_date}\n"
            f"📍 {event.location}\n\n"
            f"Kechikmang! 🙂"
        )
        return send_telegram_message(registration.user.telegram_chat_id, reminder_msg)
    except Exception as exc:
        logger.error(f"Error in notify_event_reminder({registration_id}): {exc}")
        return False
