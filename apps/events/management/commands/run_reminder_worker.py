import time
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Eslatmalarni davriy ravishda tekshiruvchi fon xizmati (Periodic reminder worker)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=300,
            help="Tekshiruvlar oralig'i (soniyalarda, default: 300 soniya / 5 daqiqa)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        self.stdout.write(
            self.style.SUCCESS(
                f"Evently eslatmalar fon xizmati (Reminder Worker) ishga tushdi. Oraliq: {interval}s"
            )
        )
        while True:
            try:
                call_command("send_event_reminders")
            except Exception as exc:
                self.stderr.write(f"Eslatma yuborishda xatolik yuz berdi: {exc}")
            time.sleep(interval)
