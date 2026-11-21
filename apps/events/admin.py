from django.contrib import admin
from .models import Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "event_type",
        "start_at",
        "end_at",
        "capacity",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("event_type", "status", "start_at")
    search_fields = ("title", "description", "location")
    ordering = ("start_at",)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "event",
        "status",
        "reminder_sent",
        "created_at",
        "cancelled_at",
    )
    list_filter = ("status", "reminder_sent", "created_at")
    search_fields = ("user__email", "event__title")
    ordering = ("-created_at",)
