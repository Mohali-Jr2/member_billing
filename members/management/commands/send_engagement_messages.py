from django.core.management.base import BaseCommand
from django.utils import timezone

from members.models import Member, NotificationLog
from members.notifications import send_member_reminder


class Command(BaseCommand):
    help = "Send engagement messages such as birthday greetings."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show messages without sending them.")

    def handle(self, *args, **options):
        today = timezone.localdate()
        birthday_members = Member.objects.filter(
            is_active=True,
            date_of_birth__month=today.month,
            date_of_birth__day=today.day,
        )

        if not birthday_members:
            self.stdout.write(self.style.SUCCESS("No engagement messages are due."))
            return

        for member in birthday_members:
            if options["dry_run"]:
                self.stdout.write(f"[DRY RUN] Birthday message: {member.full_name}")
                continue
            _, _, results = send_member_reminder(member, NotificationLog.KIND_BIRTHDAY, today)
            self.stdout.write(f"Processed birthday message for {member.full_name}: {len(results)} channel(s).")
