from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.events.models import Event, Registration

User = get_user_model()


class Command(BaseCommand):
    help = "Test uchun namunaviy ma'lumotlar yaratish (2 admin, 10 user, 15 tadbir)"

    def handle(self, *args, **options):
        self.stdout.write("Namunaviy ma'lumotlar yaratilmoqda...")

        # 1. Admins
        admin1, _ = User.objects.get_or_create(
            email="admin1@example.com",
            defaults={
                "first_name": "Admin",
                "last_name": "Birinchi",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin1.set_password("AdminPass123!")
        admin1.save()

        admin2, _ = User.objects.get_or_create(
            email="admin2@example.com",
            defaults={
                "first_name": "Admin",
                "last_name": "Ikkinchi",
                "role": User.Role.ADMIN,
                "is_staff": True,
            },
        )
        admin2.set_password("AdminPass123!")
        admin2.save()

        # 2. Users
        users = []
        for i in range(1, 11):
            user, _ = User.objects.get_or_create(
                email=f"user{i}@example.com",
                defaults={
                    "first_name": f"Foydalanuvchi{i}",
                    "last_name": f"Familya{i}",
                    "phone_number": f"+9989012345{i:02d}",
                    "role": User.Role.USER,
                },
            )
            user.set_password("UserPass123!")
            user.save()
            users.append(user)

        # 3. Events
        now = timezone.now()
        event_types = [Event.EventType.SEMINAR, Event.EventType.MASTERCLASS, Event.EventType.TRAINING]
        
        events = []
        for i in range(1, 16):
            start = now + timedelta(days=i, hours=2)
            end = start + timedelta(hours=3)
            event, _ = Event.objects.get_or_create(
                title=f"Tadbir #{i}: {event_types[i % 3].capitalize()} bo'yicha amaliy dars",
                defaults={
                    "description": f"Bu #{i}-raqamli amaliy tadbir tavsifi. Ko'nikmalarni oshirish uchun mo'ljallangan.",
                    "event_type": event_types[i % 3],
                    "location": f"IT Park, {i}-bino, {100+i}-xona",
                    "start_at": start,
                    "end_at": end,
                    "capacity": 20 if i % 2 == 0 else None,
                    "status": Event.Status.OPEN,
                    "created_by": admin1,
                },
            )
            events.append(event)

        # 4. Registrations
        for i in range(min(len(users), len(events))):
            Registration.objects.get_or_create(
                user=users[i],
                event=events[i],
                defaults={"status": Registration.Status.ACTIVE},
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Namunaviy ma'lumotlar muvaffaqiyatli yaratildi! (2 admin, 10 user, 15 tadbir)"
            )
        )
