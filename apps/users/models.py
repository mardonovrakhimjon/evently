from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

phone_regex = RegexValidator(
    regex=r"^\+998\d{9}$",
    message="Telefon raqami '+998XXXXXXXXX' formatida bo'lishi kerak.",
)


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for auth."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email manzili ko'rsatilishi shart."))
        email = self.normalize_email(email)
        extra_fields.setdefault("role", User.Role.USER)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser is_staff=True bo'lishi shart."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser is_superuser=True bo'lishi shart."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "User"

    username = None
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    phone_number = models.CharField(
        _("phone number"),
        max_length=20,
        blank=True,
        validators=[phone_regex],
    )
    role = models.CharField(
        _("role"),
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    telegram_chat_id = models.BigIntegerField(
        _("telegram chat id"),
        null=True,
        blank=True,
        unique=True,
    )
    telegram_link_token = models.CharField(
        _("telegram link token"),
        max_length=64,
        null=True,
        blank=True,
        unique=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.email

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)
