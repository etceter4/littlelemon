from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Creates the required user groups'

    def handle(self, *args, **kwargs):
        groups = ['Admin', 'Manager', 'Delivery Crew']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
            self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created or already exists.'))
