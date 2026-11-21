from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException
from apps.events.models import Event, Registration
from apps.notifications.services import notify_registration


class BusinessLogicError(APIException):
    status_code = 400

    def __init__(self, detail: str, code: str):
        super().__init__(detail=detail, code=code)
        self.detail = {"detail": detail, "code": code}


def register_for_event(user, event_id: int) -> Registration:
    """
    Registers a user for an event according to BR-1, BR-2, BR-3, BR-5.
    Thread-safe with select_for_update() to prevent race conditions.
    """
    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(pk=event_id)
        except Event.DoesNotExist:
            raise BusinessLogicError("Tadbir topilmadi.", "event_not_found")

        # BR-5: Yopilgan tadbirga yozilish mumkin emas
        if event.status == Event.Status.CLOSED:
            raise BusinessLogicError("Tadbir yopilgan.", "event_closed")

        # BR-3: Tugagan/boshlangan tadbirga yozilish mumkin emas
        if event.start_at <= timezone.now():
            raise BusinessLogicError(
                "Tadbir allaqachon boshlangan.", "event_started"
            )

        # Check existing registration
        registration = (
            Registration.objects.select_for_update()
            .filter(user=user, event=event)
            .first()
        )

        # BR-1: Foydalanuvchi allaqachon faol yozilgan bo'lsa rad etiladi
        if registration and registration.status == Registration.Status.ACTIVE:
            raise BusinessLogicError(
                "Siz bu tadbirga allaqachon yozilgansiz.", "already_registered"
            )

        # BR-2: Cheklangan joy tekshiruvi
        if event.capacity is not None:
            active_count = event.registrations.filter(
                status=Registration.Status.ACTIVE
            ).count()
            if active_count >= event.capacity:
                raise BusinessLogicError("Bo‘sh joy qolmagan.", "event_full")

        if registration:
            # Reactivate cancelled registration
            registration.status = Registration.Status.ACTIVE
            registration.cancelled_at = None
            registration.reminder_sent = False
            registration.save(update_fields=["status", "cancelled_at", "reminder_sent"])
        else:
            registration = Registration.objects.create(
                user=user,
                event=event,
                status=Registration.Status.ACTIVE,
            )

        # Trigger notification after successful DB commit
        reg_id = registration.id
        transaction.on_commit(lambda: notify_registration(reg_id))

        return registration


def unregister_from_event(user, event_id: int) -> Registration:
    """
    Unregisters a user from an event according to BR-6.
    """
    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(pk=event_id)
        except Event.DoesNotExist:
            raise BusinessLogicError("Tadbir topilmadi.", "event_not_found")

        # BR-6: Tadbir boshlangandan keyin undan chiqib bo'lmaydi
        if event.start_at <= timezone.now():
            raise BusinessLogicError(
                "Tadbir allaqachon boshlangan, ro'yxatdan chiqib bo'lmaydi.",
                "event_started",
            )

        registration = (
            Registration.objects.select_for_update()
            .filter(user=user, event=event, status=Registration.Status.ACTIVE)
            .first()
        )

        if not registration:
            raise BusinessLogicError(
                "Siz bu tadbirga yozilmagansiz.", "not_registered"
            )

        registration.status = Registration.Status.CANCELLED
        registration.cancelled_at = timezone.now()
        registration.save(update_fields=["status", "cancelled_at"])

        return registration


def close_event(event_id: int) -> Event:
    """
    Closes an event so no further registrations can occur.
    """
    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(pk=event_id)
        except Event.DoesNotExist:
            raise BusinessLogicError("Tadbir topilmadi.", "event_not_found")

        event.status = Event.Status.CLOSED
        event.save(update_fields=["status"])
        return event
