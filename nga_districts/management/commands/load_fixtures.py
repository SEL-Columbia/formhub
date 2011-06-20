from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = "Load the LGAs from fixtures."

    def handle(self, *args, **kwargs):
        call_command('syncdb', interactive=False)
        
        if not os.path.exists('xform_manager_dataset.json'):
            raise Exception("Download and unpack xform_manager_dataset.json into the project dir.")
        
        for file_name in ['zone.json', 'state.json', 'lga.json']:
            path = os.path.join(['nga_districts', 'fixtures', file_name])
            call_command('loaddata', file_name)
        
        call_command('loaddata', 'xform_manager_dataset.json')
