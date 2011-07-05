from django.db import models
from collections import defaultdict
import json
import re
import datetime


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
        if '_data_source' not in d:
            return
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


class Variable(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=128, primary_key=True)
    data_type = models.CharField(max_length=20)
    description = models.CharField(max_length=255)

    FIELDS = ['name', 'slug', 'data_type', 'description']

    _cache = {}

    @classmethod
    def get_from_cache(cls, slug):
        if slug not in cls._cache:
            cls._cache[slug] = cls.objects.get(slug=slug)
        return cls._cache[slug]

    def get_casted_value(self, value):
        """
        Takes a Variable and a value and casts it to the appropriate Variable.data_type.
        """
        def get_float(x):
            return float(x)

        def get_boolean(x):
            if isinstance(x, basestring):
                regex = re.compile('(true|t|yes|y|1)', re.IGNORECASE)
                return regex.search(value) is not None
            return bool(x)

        def get_string(x):
            return unicode(x)

        cast_function = {
            'float': get_float,
            'boolean': get_boolean,
            'string': get_string
            }
        if self.data_type not in cast_function:
            raise Exception(self.__unicode__())
        return cast_function[self.data_type](value)

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.FIELDS])

    @classmethod
    def get_full_data_dictionary(cls, as_json=True):
        result = [v.to_dict() for v in cls.objects.all()]
        return result if not as_json else json.dumps(result)

    def value_field(self):
        """
        Data for this variable will be stored in a column
        with this name in a DataRecord.
        """
        return self.data_type + '_value'

    def __unicode__(self):
        return json.dumps(self.to_dict(), indent=4)


def sum_non_null_values(d, keys):
    """
    Helper function for calculated variables.
    """
    return sum([d[key] for key in keys if d[key] is not None])


class CalculatedVariable(Variable):
    """
    example formula: d['num_students_total'] / d['num_tchrs_total']

    Right now calculated variables will only be computed in
    FacilityBuilder.create_facility_from_dict
    """
    formula = models.TextField()

    FIELDS = Variable.FIELDS + ['formula']

    @classmethod
    def add_calculated_variables(cls, d):
        for cv in cls.objects.all():
            value = cv.calculate_value(d)
            if value is not None:
                d[cv.slug] = value

    def calculate_value(self, d):
        try:
            return eval(self.formula)
        except:
            return None


class DataRecord(models.Model):
    """
    Not sure if we want to use different columns for data types or do
    some django Meta:abstract=True stuff to have different subclasses of DataRecord
    behave differently. For now, this works and is pretty clean.
    """
    float_value = models.FloatField(null=True)
    boolean_value = models.NullBooleanField()
    string_value = models.CharField(null=True, max_length=255)

    TYPES = ['float', 'boolean', 'string']

    variable = models.ForeignKey(Variable)
    date = models.DateField(null=True)

    class Meta:
        abstract = True

    def get_value(self):
        return getattr(self, self.variable.data_type + "_value")

    def set_value(self, val):
        setattr(self, self.variable.data_type + "_value", val)

    value = property(get_value, set_value)

    def date_string(self):
        if self.date is None:
            return "No date"
        else:
            return self.date.strftime("%D")


class DictModel(models.Model):

    class Meta:
        abstract = True

    def set(self, variable, value, date=None):
        """
        This is used to add a data record of type variable to the instance.
        It returns the casted value for the variable.
        """
        if date is None:
            date = datetime.date.today()
        kwargs = {
            'variable': variable,
            self._data_record_fk: self,
            'date': date,
            }
        d, created = self._data_record_class.objects.get_or_create(**kwargs)
        d.value = variable.get_casted_value(value)
        d.save()
        return d.value

    def add_data_from_dict(self, d):
        """
        Key value pairs in d that are in the data dictionary will be
        added to the database along with any calculated variables that apply.
        """
        for v in Variable.objects.all():
            if v.slug in d:
                # update the dict with the casted value
                d[v.slug] = self.set(v, d[v.slug])

        CalculatedVariable.add_calculated_variables(d)
        for cv in CalculatedVariable.objects.all():
            if cv.slug in d:
                self.set(cv, d[cv.slug])

    def _kwargs(self):
        """
        To get all data records associated with a facility or lga we need to
        filter FacilityRecords or LGARecords that link to this facility or
        lga. Awesome doc string!
        """
        return {self._data_record_fk: self}

    def get_all_data(self):
        records = self._data_record_class.objects.filter(**self._kwargs())
        d = defaultdict(dict)
        for record in records:
            d[record.variable.slug][record.date.isoformat()] = record.value
        return d

    def get_latest_data(self):
        records = self._data_record_class.objects.filter(**self._kwargs()).order_by('-date')
        d = {}
        for r in records:
            # todo: test to make sure this sorting is correct
            if r.variable.slug not in d:
                d[r.variable.slug] = r.value
        return d

    def get_latest_value_for_variable(self, variable):
        if type(variable) == str:
            variable = Variable.objects.get(slug=variable)
        try:
            kwargs = self._kwargs()
            kwargs['variable'] = variable
            record = self._data_record_class.objects.filter(**kwargs).order_by('-date')[0]
        except IndexError:
            return None
        return record.value

    def dates(self):
        """
        Return a list of dates of all observations for this DictModel.
        """
        drs = self._data_record_class.objects.filter(**self._kwargs()).values('date').distinct()
        return [d['date'] for d in drs]
