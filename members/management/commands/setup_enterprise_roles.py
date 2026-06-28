from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create Patron and Treasurer role groups for the billing system."

    def handle(self, *args, **options):
        roles = {
            "Patron": Permission.objects.filter(codename__startswith="view_"),
            "Treasurer": Permission.objects.filter(content_type__app_label="members"),
        }

        for name, permissions in roles.items():
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"Configured role: {name}"))
