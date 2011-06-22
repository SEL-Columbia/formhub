from django.db import models
from collections import defaultdict
import datetime
import json

from nga_districts.models import LGA


class Facility(models.Model):
    """
    TODO: Figure out what fields should actually be on a facility. I think all
    fields should be stored in data records, with convenience fields stored in
    the facility model as needed.
    """
    ftype = models.ForeignKey('FacilityType', related_name="facilities")
    facility_id = models.CharField(max_length=100)
#    survey_instance = models.ForeignKey('Instance', related_name="facilities", null=True)
    lga = models.ForeignKey(LGA, related_name="facilities", null=True)
    
    def set(self, variable, value, date=None):
        if date is None:
            date = datetime.date.today()
        d, created = DataRecord.objects.get_or_create(variable=variable, facility=self, date_value=date)
        d.value=value
        d.save()

    def get_all_data(self):
        records = DataRecord.objects.filter(facility=self)
        d = defaultdict(dict)
        for r in records:
            d[record.variable.slug][record.date] = record.value
    
    def get_latest_value_for_variable(self, variable):
        try:
            variable = DataRecord.objects.filter(facility=self, variable=variable).order_by('-date_value')[0]
        except IndexError:
            variable = None
        return variable
    
    def _ordered_records_for_date(self, date):
        #kindof a hack to get dates displaying in tables
        variables = self.ftype.ordered_variables
        records = []
        for v in variables:
            try:
                dr = DataRecord.objects.get(date_value=date, variable=v, facility=self)
            except DataRecord.DoesNotExist:
                dr = None
            records.append(dr)
        return records
    
    def set_value(self, variable, value):
        d, created = DataRecord.objects.get_or_create(variable=variable, facility=self)
        d.value = value
        d.save()
    
    def values_in_order(self):
        return [self.get_latest_value_for_variable(v) for v in self.ftype.ordered_variables]
    
    def dates(self):
        drs = DataRecord.objects.filter(facility=self).values('date_value').distinct()
        return [d['date_value'] for d in drs]

    @classmethod
    def get_latest_data_by_lga(cls, lga):
        d = defaultdict(dict)
        records = DataRecord.objects.filter(facility__lga=lga).order_by('variable__slug', '-date_value')
        for r in records:
            # todo: test to make sure this sorting is correct
            if r.variable.slug not in d[r.facility.id]:
                d[r.facility.id][r.variable.slug] = r.value
        return d


class Variable(models.Model):
    name = models.CharField(max_length=64)
    slug = models.CharField(max_length=64)
    data_type = models.CharField(max_length=20)
    description = models.CharField(max_length=255)
    xpath = models.CharField(max_length=50)

    FIELDS = ['name', 'slug', 'data_type', 'description', 'xpath']
    
    def calculate_total_for_lga(self, lga):
        if self.data_type == "string":
            return None
        else:
            records = DataRecord.objects.filter(variable=self, facility__lga=lga)
            tot = 0
            for record in records:
                tot += record.value
            return tot
    
    def calculate_average_for_lga(self, lga):
        if self.data_type == "string":
            return None
        else:
            records = DataRecord.objects.filter(variable=self, facility__lga=lga)
            count = records.count()
            if count == 0:
                return 0
            tot = 0
            for record in records:
                tot += record.value
            return tot / count

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.FIELDS])

    def __unicode__(self):
        return json.dumps(self.to_dict(), indent=4)

class DataRecord(models.Model):
    """
    Not sure if we want to use different columns for data types or do
    some django Meta:abstract=True stuff to have different subclasses of DataRecord
    behave differently. For now, this works and is pretty clean.
    """
    float_value = models.FloatField(null=True)
    boolean_value = models.NullBooleanField()
    string_value = models.CharField(null=True, max_length=255)

    variable = models.ForeignKey(Variable, related_name="data_records")
    facility = models.ForeignKey(Facility, related_name="data_records")
    date_value = models.DateField(null=True)

    TYPES = ['float', 'boolean', 'string']

    def get_data_type(self):
        return self.variable.data_type
    data_type = property(get_data_type)
    
    def get_value(self):
        return getattr(self, self.data_type + "_value")
    
    def set_value(self, val):
        setattr(self, self.data_type + "_value", val)
    
    value = property(get_value, set_value)

    def date_string(self):
        if self.date_value is None:
            return "No date"
        else:
            return self.date_value.strftime("%D")


class FacilityType(models.Model):
    """
    A model to hold data specific to the FacilityType (...in MVIS this was the Sector)
    """
    name = models.CharField(max_length=20)
    slug = models.SlugField()
    variables = models.ManyToManyField(Variable, related_name="facility_types")
    variable_order_json = models.TextField(null=True)
    
    _ordered_variables = None
    def get_ordered_variables(self):
        """
        Order of variables is something that came up *a lot* in MVIS.
        
        The (fugly) code below uses self.variables (m2m field) but orders
        the results based on the JSON list of ids in "variable_order_json".
        """
        if self._ordered_variables is not None:
            return self._ordered_variables
        #I think it makes sense to pull all the variables into memory.
        variables = list(self.variables.all())
        if self.variable_order_json is None:
            ordered_ids = []
        else:
            import json
            ordered_ids = json.loads(self.variable_order_json)
        #aack... fugly code below
        n_ordered_variables = []
        for vid in ordered_ids:
            try:
                found_variable = [z for z in variables if z.id==vid][0]
                variables.pop(variables.index(found_variable))
                n_ordered_variables.append(found_variable)
            except IndexError:
                pass
        self._ordered_variables = n_ordered_variables + variables
        return self._ordered_variables
    ordered_variables = property(get_ordered_variables)
    
    def set_variable_order(self, variable_list, autosave=True):
        if len(variable_list)==0:
            return
        if isinstance(variable_list[0], int):
            variable_id_list = variable_list
        else:
            variable_id_list = [v.id for v in variable_list]
        import json
        self.variable_order_json = json.dumps(variable_id_list)
        self._ordered_variables = None
        if autosave:
            self.save()


class KeyRename(models.Model):
    data_source = models.CharField(max_length=64)
    old_key = models.CharField(max_length=64)
    new_key = models.CharField(max_length=64)

    class Meta:
        unique_together = (("data_source", "old_key"),)

    @classmethod
    def _get_rename_dictionary(cls, data_source):
        result = {}
        for key_rename in cls.objects.filter(data_source=data_source):
            result[key_rename.old_key] = key_rename.new_key
        return result

    @classmethod
    def rename_keys(cls, d):
        """
        Apply the rename rules saved in the database to the dict
        d. Assumes that the key '_data_source' is in d.
        """
        temp = {}
        rename_dictionary = cls._get_rename_dictionary(d['_data_source'])
        for k, v in rename_dictionary.items():
            if k in d:
                temp[v] = d[k]
                del d[k]
            else:
                print "rename rule '%s' not used in data source '%s'" % \
                    (k, d['_data_source'])
        # this could overwrite keys that weren't renamed
        d.update(temp)


from xform_manager.models import Instance
from django.db.models.signals import post_save
from facility_builder import FacilityBuilder

def create_facility_from_signal(sender, **kwargs):
    survey_instance = kwargs["instance"]
    FacilityBuilder.create_facility_from_instance(survey_instance)

post_save.connect(create_facility_from_signal, sender=Instance)
