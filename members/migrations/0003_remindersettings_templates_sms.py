import django.core.validators
from django.db import migrations, models


def create_default_reminder_records(apps, schema_editor):
    ReminderSetting = apps.get_model("members", "ReminderSetting")
    MessageTemplate = apps.get_model("members", "MessageTemplate")

    ReminderSetting.objects.get_or_create(pk=1)
    MessageTemplate.objects.get_or_create(
        kind="MONTHLY_START",
        defaults={
            "subject": "New month billing reminder",
            "body": (
                "Hello {full_name}, a new billing month has started. "
                "Your current outstanding balance is UGX {balance}. "
                "Please make your payment as soon as possible. Thank you."
            ),
        },
    )
    MessageTemplate.objects.get_or_create(
        kind="FOUR_MONTH_REMINDER",
        defaults={
            "subject": "Four month payment reminder",
            "body": (
                "Hello {full_name}, this is a reminder for your 4-month payment plan. "
                "Your current outstanding balance is UGX {balance}. "
                "Please pay to keep your membership up to date. Thank you."
            ),
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0002_notificationlog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationlog",
            name="channel",
            field=models.CharField(choices=[("EMAIL", "Email"), ("WHATSAPP", "WhatsApp"), ("SMS", "SMS")], max_length=20),
        ),
        migrations.CreateModel(
            name="ReminderSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("monthly_reminder_day", models.PositiveSmallIntegerField(default=1)),
                ("enable_email", models.BooleanField(default=True)),
                ("enable_whatsapp", models.BooleanField(default=True)),
                ("enable_sms_fallback", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Reminder setting",
                "verbose_name_plural": "Reminder settings",
            },
        ),
        migrations.CreateModel(
            name="MessageTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("MONTHLY_START", "New month reminder"), ("FOUR_MONTH_REMINDER", "Four month payment reminder")], max_length=40, unique=True)),
                ("subject", models.CharField(max_length=160)),
                ("body", models.TextField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["kind"],
            },
        ),
        migrations.RunPython(create_default_reminder_records, migrations.RunPython.noop),
    ]
