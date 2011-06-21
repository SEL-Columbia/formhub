from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

from facilities.models import *

#from django.contrib.auth.models import User

import json

class Command(BaseCommand):
    help = "Load the LGAs from fixtures."

    def handle(self, *args, **kwargs):
        call_command('syncdb', interactive=False)
        
        if not os.path.exists('xform_manager_dataset.json'):
            raise Exception("Download and unpack xform_manager_dataset.json into the project dir.")
        
        for file_name in ['zone.json', 'state.json', 'lga.json']:
            path = os.path.join(['nga_districts', 'fixtures', file_name])
            call_command('loaddata', file_name)
        
        with open('facilities/variables/variables.json', 'r') as f:
            vdata = json.loads(f.read())
            for variable in vdata:
                v, created = Variable.objects.get_or_create(**variable)
        call_command('loaddata', 'xform_manager_dataset.json')
        
        #create an admin user...
        from django.contrib.auth.models import User
        admin = User.objects.create(
            username="admin",
            email="admin@admin.com",
            is_staff=True,
            is_superuser=True
            )
        admin.set_password("pass")
        admin.save()
