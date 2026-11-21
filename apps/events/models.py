from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Event(models.Model):
    class EventType(models.TextChoices):
        SEMINAR = "seminar", "Seminar"
        MASTERCLASS = "masterclass", "Masterclass"
        TRAINING = "training", "Training"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(_("title"), max_length=200)
    description = models.TextField(_("description"))
    event_type = models.CharField(
        _("event type"),
        max_length=20,
        choices=EventType.choices,
    )
    location = models.CharField(_("location"), max_length=255)
    start_at = models.DateTimeField(_("start at"))
    end_at = models.DateTimeField(_("end at"))
    capacity = models.PositiveIntegerField(
        _("capacity"),
        null=True,
        blank=True,
        help_text=_("null = cheklanmagan joylar"),
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["start_at"]

    def __str__(self):
        return self.title

    @property
    def is_finished(self):
        return self.end_at < timezone.now()

    @property
    def is_started(self):
        return self.start_at <= timezone.now()

    def get_registered_count(self):
        # Used as fallback if not annotated with registered_count
        if hasattr(self, "annotated_registered_count"):
            return self.annotated_registered_count
        return self.registrations.filter(status=Registration.Status.ACTIVE).count()

    def get_available_seats(self):
        if self.capacity is None:
            return None
        count = self.get_registered_count()
        return max(0, self.capacity - count)


class Registration(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("user"),
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("event"),
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    reminder_sent = models.BooleanField(
        _("reminder sent"),
        default=False,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    cancelled_at = models.DateTimeField(_("cancelled at"), null=True, blank=True)

    class Meta:
        verbose_name = _("registration")
        verbose_name_plural = _("registrations")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                name="unique_user_event_registration",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.event.title} ({self.status})"
