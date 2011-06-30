from django.db import models
from django.db.models import Max
from collections import defaultdict
import sys

from nga_districts.models import LGA
from abstract_models import Variable, CalculatedVariable, DataRecord, DictModel, KeyRename


class FacilityRecord(DataRecord):
    facility = models.ForeignKey('Facility', related_name='data_records')

    @classmethod
    def counts_by_variable(cls, lga):
        records = cls.objects.filter(facility__lga=lga).values('facility', 'variable', 'float_value', 'boolean_value', 'string_value', 'facility__sector').annotate(Max('date')).distinct()
        def infinite_dict():
            return defaultdict(infinite_dict)
        result = infinite_dict()
        for d in records:
            variable = Variable.get_from_cache(d['variable'])
            value = '%s_value' % variable.data_type
            if d[value] in result[d['facility__sector']][d['variable']]:
                result[d['facility__sector']][d['variable']][d[value]] += 1
            else:
                result[d['facility__sector']][d['variable']][d[value]] = 1
        return result

    @classmethod
    def counts_of_boolean_variables(cls, lga):
        result = cls.counts_by_variable(lga)
        for sector, d in result.items():
            for k, v in d.items():
                variable = Variable.get_from_cache(k)
                if variable.data_type != 'boolean':
                    del d[k]
        return result

    @classmethod
    def count_by_lga(cls, variable):
        value = '%s_value' % variable.data_type
        records = cls.objects.filter(variable=variable).values('facility__lga', 'facility', value).annotate(Max('date')).distinct()
        result = defaultdict(dict)
        for d in records:
            try:
                result[d['facility__lga']][d[value]] += 1
            except KeyError:
                result[d['facility__lga']][d[value]] = 1
        return result


class Sector(models.Model):
    slug = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=128)


class Facility(DictModel):
    """
    TODO: Figure out what fields should actually be on a facility. I think all
    fields should be stored in data records, with convenience fields stored in
    the facility model as needed.
    """
    facility_id = models.CharField(max_length=100)
    lga = models.ForeignKey(LGA, related_name="facilities", null=True)
    sector = models.ForeignKey(Sector, null=True)

    _data_record_class = FacilityRecord
    _data_record_fk = 'facility'

    @classmethod
    def get_latest_data_by_lga(cls, lga):
        d = defaultdict(dict)
#        records = FacilityRecord.objects.filter(facility__lga=lga).order_by('variable__slug', '-date')
        records = FacilityRecord.objects.filter(facility__lga=lga).order_by('-date')
        for r in records:
            # todo: test to make sure this sorting is correct
#            if r.variable.slug not in d[r.facility.id]:
#                d[r.facility.id][r.variable.slug] = r.value
            if r.variable_id not in d[r.facility_id]:
                d[r.facility_id][r.variable_id] = r.value
        return d

    @classmethod
    def calculate_total_for_lga(self, lga):
        if self.data_type == "string":
            return None
        else:
            records = FacilityRecord.objects.filter(variable=self, facility__lga=lga)
            tot = 0
            for record in records:
                tot += record.value
            return tot

    @classmethod
    def calculate_average_for_lga(self, lga):
        if self.data_type == "string":
            return None
        else:
            records = FacilityRecord.objects.filter(variable=self, facility__lga=lga)
            count = records.count()
            if count == 0:
                return 0
            tot = 0
            for record in records:
                tot += record.value
            return tot / count


from xform_manager.models import Instance
from django.db.models.signals import post_save
from facility_builder import FacilityBuilder

def create_facility_from_signal(sender, **kwargs):
    survey_instance = kwargs["instance"]
    try:
        FacilityBuilder.create_facility_from_instance(survey_instance)
    except:
        print "Unexpected error:", sys.exc_info()[0]

post_save.connect(create_facility_from_signal, sender=Instance)
