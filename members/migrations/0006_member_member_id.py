from django.db import migrations, models


def populate_member_ids(apps, schema_editor):
    Member = apps.get_model("members", "Member")
    for member in Member.objects.all().order_by("pk"):
        if not member.member_id:
            member.member_id = f"MB{member.pk:06d}"
            member.save(update_fields=["member_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0005_member_date_of_birth_member_user_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="member_id",
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
        migrations.RunPython(populate_member_ids, migrations.RunPython.noop),
    ]
