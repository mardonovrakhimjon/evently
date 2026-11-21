from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "role",
        "phone_number",
        "telegram_chat_id",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name", "phone_number")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "role",
                    "telegram_chat_id",
                    "telegram_link_token",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "role",
                ),
            },
        ),
    )
