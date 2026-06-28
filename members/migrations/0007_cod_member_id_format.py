from django.db import migrations


def convert_to_cod_member_ids(apps, schema_editor):
    Member = apps.get_model("members", "Member")
    for member in Member.objects.all().order_by("pk"):
        member.member_id = f"COD-{member.pk:06d}"
        member.save(update_fields=["member_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0006_member_member_id"),
    ]

    operations = [
        migrations.RunPython(convert_to_cod_member_ids, migrations.RunPython.noop),
    ]
