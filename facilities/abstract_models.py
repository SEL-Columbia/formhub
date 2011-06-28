from django.db import models
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
#    slug = models.CharField(max_length=64, unique=True)
    slug = models.CharField(max_length=128, primary_key=True)
    data_type = models.CharField(max_length=20)
    description = models.CharField(max_length=255)

    FIELDS = ['name', 'slug', 'data_type', 'description']

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

    def __unicode__(self):
        return json.dumps(self.to_dict(), indent=4)


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

    def add_data_from_dict(self, d):
        """
        Key value pairs in d that are in the data dictionary will be
        added to the database.
        """
        KeyRename.rename_keys(d)
        CalculatedVariable.add_calculated_variables(d)

        for v in Variable.objects.all():
            if v.slug in d:
                self.set(v, d[v.slug])
