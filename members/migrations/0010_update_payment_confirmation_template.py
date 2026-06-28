from django.db import migrations


OLD_PAYMENT_CONFIRMATION_BODY = (
    "Hello {full_name}, your payment has been recorded. "
    "Your current outstanding balance is UGX {balance}. Thank you."
)

NEW_PAYMENT_CONFIRMATION_BODY = (
    "Hello {full_name}, your payment of UGX {payment_amount} "
    "paid on {payment_date} has been attached to your account. "
    "Reference: {payment_reference}. Your current outstanding "
    "balance is UGX {balance}. Thank you."
)


def update_payment_confirmation_template(apps, schema_editor):
    MessageTemplate = apps.get_model("members", "MessageTemplate")
    MessageTemplate.objects.filter(
        kind="PAYMENT_CONFIRMATION",
        body=OLD_PAYMENT_CONFIRMATION_BODY,
    ).update(body=NEW_PAYMENT_CONFIRMATION_BODY)


class Migration(migrations.Migration):
    dependencies = [
        ("members", "0009_four_digit_cod_member_id"),
    ]

    operations = [
        migrations.RunPython(update_payment_confirmation_template, migrations.RunPython.noop),
    ]
