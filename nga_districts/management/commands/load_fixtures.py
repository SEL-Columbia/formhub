from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from facilities.models import Variable


class Command(BaseCommand):
    help = "Load the LGAs from fixtures."

    def handle(self, *args, **kwargs):
        call_command('syncdb', interactive=False)
        self.load_lgas()
        self.create_variables()
        self.load_surveys()
        self.create_admin_user()

    def load_lgas(self):
        for file_name in ['zone.json', 'state.json', 'lga.json']:
            call_command('loaddata', file_name)

    def create_variables(self):
        from utils.csv_reader import CsvReader
        path = os.path.join('facilities', 'fixtures', 'variables.csv')
        csv_reader = CsvReader(path)
        for d in csv_reader.iter_dicts():
            Variable.objects.get_or_create(**d)

    def load_surveys(self):
        if not os.path.exists('xform_manager_dataset.json'):
            raise Exception("Download and unpack xform_manager_dataset.json into project dir.")
        call_command('loaddata', 'xform_manager_dataset.json')

    def create_admin_user(self):
        from django.contrib.auth.models import User
        admin, created = User.objects.get_or_create(
            username="admin",
            email="admin@admin.com",
            is_staff=True,
            is_superuser=True
            )
        admin.set_password("pass")
        admin.save()
