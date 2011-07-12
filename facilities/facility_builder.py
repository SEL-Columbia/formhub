import json
import uuid
from nga_districts.models import LGA
from facilities.models import Facility, Variable, KeyRename, \
    CalculatedVariable, Sector


class FacilityBuilder(object):
    """
    facility_builder.py is where we'll have code to convert a
    dictionary into a facility with data. This will allow us to load
    facilities from survey data or from csv files.
    """

    SURVEYS_WITH_FACILITIES = ['Health', 'Water', 'Education']

    @classmethod
    def create_facility_from_dict(cls, d):
        """
        Requires facility type and lga to be specified in d, all other
        key value pairs in d that are in the data dictionary will be
        added to the database.
        """
        KeyRename.rename_keys(d)

        # using gps as facility id is a slight hack to get a unique id
        kwargs = {
            'facility_id': d.get('gps', uuid.uuid4())
            }
        if '_lga_id' in d:
            try:
                kwargs['lga'] = LGA.objects.get(id=d['_lga_id'])
            except LGA.DoesNotExist, e:
                pass
        if '_facility_type' in d:
            try:
                kwargs['sector'] = Sector.objects.get(
                   slug=d['_facility_type'].lower())
            except Sector.DoesNotExist, e:
                pass
        facility, created = Facility.objects.get_or_create(**kwargs)
        facility.add_data_from_dict(d)

        return facility

    @classmethod
    def print_dict(cls, d):
        print json.dumps(d, indent=4, sort_keys=True)

    @classmethod
    def create_facility_from_instance(cls, survey_instance):
        # When an instance is saved, first delete the parsed_instance
        # associated with it.
        idict = survey_instance.get_dict()

        def add_survey_type_from_xform_id_string(d):
            l = d['_xform_id_string'].split("_")
            d['_survey_type'] = l[0]
        add_survey_type_from_xform_id_string(idict)

        if idict['_survey_type'] not in cls.SURVEYS_WITH_FACILITIES:
            return

        def add_lga_id(d):
            try:
                zone = d['location/zone']
                state = d['location/state_in_%s' % zone]
                lga = d['location/lga_in_%s' % state]
                d['_lga_id'] = LGA.objects.get(slug=lga, state__slug=state).id
            except KeyError:
                raise Exception(d)
        add_lga_id(idict)

        def add_data_source(d):
            d['_data_source'] = d['_xform_id_string']
        add_data_source(idict)

        return cls.create_facility_from_dict(idict)
