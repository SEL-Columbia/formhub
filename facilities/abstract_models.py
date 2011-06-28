from django.db import models
import json
import re


class Variable(models.Model):
    name = models.CharField(max_length=64)
#    slug = models.CharField(max_length=64, unique=True)
    slug = models.CharField(max_length=64, primary_key=True)
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

    def calculate_value(self, d):
        # TODO: eval lol
        val = None
        try:
            val = eval(self.formula)
        except:
            pass
        return val


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

    variable = models.ForeignKey(Variable, related_name="data_records")
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
