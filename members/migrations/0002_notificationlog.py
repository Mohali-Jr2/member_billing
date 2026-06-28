from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(choices=[("EMAIL", "Email"), ("WHATSAPP", "WhatsApp")], max_length=20)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("MONTHLY_START", "New month reminder"),
                            ("FOUR_MONTH_REMINDER", "Four month payment reminder"),
                        ],
                        max_length=40,
                    ),
                ),
                ("event_date", models.DateField()),
                ("status", models.CharField(choices=[("SENT", "Sent"), ("FAILED", "Failed")], max_length=20)),
                ("message", models.TextField()),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_logs",
                        to="members.member",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="notificationlog",
            constraint=models.UniqueConstraint(
                fields=("member", "channel", "kind", "event_date"),
                name="unique_member_notification_per_event",
            ),
        ),
    ]
