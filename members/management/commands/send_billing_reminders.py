from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from members.models import Member, MessageTemplate, NotificationLog, ReminderSetting
from members.notifications import send_member_reminder


class Command(BaseCommand):
    help = "Send WhatsApp and email billing reminders to active members."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show reminders without sending them.")
        parser.add_argument(
            "--date",
            help="Run reminders for a specific date in YYYY-MM-DD format. Defaults to today.",
        )

    def handle(self, *args, **options):
        run_date = self._get_run_date(options.get("date"))
        dry_run = options["dry_run"]
        MessageTemplate.ensure_defaults()
        reminders = list(self._build_reminders(run_date))

        if not reminders:
            self.stdout.write(self.style.SUCCESS("No billing reminders are due."))
            return

        for member, kind, subject, message in reminders:
            if dry_run:
                self.stdout.write(f"[DRY RUN] {member.full_name}: {subject}")
                continue

            _, _, results = send_member_reminder(member, kind, run_date)
            for result in results:
                output = f"{result['status']}: {result['channel']} reminder for {member.full_name}"
                if result["error"]:
                    output += f" ({result['error']})"
                self.stdout.write(output)

        self.stdout.write(self.style.SUCCESS(f"Processed {len(reminders)} billing reminder(s)."))

    def _get_run_date(self, date_value):
        if date_value:
            return timezone.datetime.fromisoformat(date_value).date()
        return timezone.localdate()

    def _build_reminders(self, run_date):
        members = Member.objects.filter(is_active=True).order_by("full_name")
        for member in members:
            balance = member.balance()
            if balance <= 0:
                continue

            setting = ReminderSetting.current()
            if run_date.day == setting.monthly_reminder_day:
                template = MessageTemplate.objects.get(kind=NotificationLog.KIND_MONTHLY_START)
                yield (
                    member,
                    NotificationLog.KIND_MONTHLY_START,
                    template.render_subject(member),
                    template.render_body(member),
                )

            months_due = member.months_due_on(run_date)
            previous_months_due = member.months_due_on(run_date - timedelta(days=1))
            entered_fourth_month = months_due != previous_months_due and months_due > 0 and months_due % 4 == 0
            if member.plan == Member.PLAN_FOUR_MONTHS and entered_fourth_month:
                template = MessageTemplate.objects.get(kind=NotificationLog.KIND_FOUR_MONTH_REMINDER)
                yield (
                    member,
                    NotificationLog.KIND_FOUR_MONTH_REMINDER,
                    template.render_subject(member),
                    template.render_body(member),
                )
