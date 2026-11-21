from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.events.models import Event, Registration
from apps.notifications.services import notify_event_reminder


class Command(BaseCommand):
    help = "Tadbir boshlanishidan oldin qatnashuvchilarga Telegram orqali eslatma yuborish"

    def handle(self, *args, **options):
        now = timezone.now()
        hours_before = getattr(settings, "REMINDER_HOURS_BEFORE", 24)
        threshold = now + timedelta(hours=hours_before)

        # Active registrations whose event is open and starting between now and threshold
        registrations = (
            Registration.objects.select_related("user", "event")
            .filter(
                status=Registration.Status.ACTIVE,
                reminder_sent=False,
                event__status=Event.Status.OPEN,
                event__start_at__gt=now,
                event__start_at__lte=threshold,
            )
        )

        sent_count = 0
        total = registrations.count()
        self.stdout.write(f"Eslatma yuborilishi kerak bo'lgan registrationlar soni: {total}")

        for reg in registrations:
            # Send reminder if user has telegram_chat_id
            if reg.user.telegram_chat_id:
                notify_event_reminder(reg.id)
                sent_count += 1
            # Mark reminder_sent to True to avoid duplicate sending
            reg.reminder_sent = True
            reg.save(update_fields=["reminder_sent"])

        self.stdout.write(
            self.style.SUCCESS(f"Muvaffaqiyatli yakunlandi. Yuborilgan eslatmalar: {sent_count}")
        )
