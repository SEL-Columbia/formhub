from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import random
from facilities.models import *
import datetime

class Command(BaseCommand):
    help = 'Loads data into facilities spike app'

    def handle(self, *args, **options):
        call_command("syncdb", interactive=False)
        call_command("loaddata", "facilities/fixtures/fixtures.json")
        facilities = Facility.objects.all()
        variables = Variable.objects.all()
        
        possible_strings = "A B C D F".split(" ")
        
        def load_data_for_facility_variable_date(facility, variable, date):
            if variable.data_type == "string":
                ri = random.randint(0, len(possible_strings)-1)
                r = possible_strings[ri]
            elif variable.data_type == "integer":
                r = random.randint(0, 100)
            else:
                r = round(random.random() * 100, 2)
            facility.set_value_for_variable_and_date(variable, date, r)
        
        dates = []
        one_day = datetime.timedelta(1)
        today = datetime.date.today()
        for i in range(0,5):
            dates.append(today - (i*one_day))
        
        for facility in facilities:
            for variable in variables:
                for date in dates:
                    load_data_for_facility_variable_date(facility, variable, date)