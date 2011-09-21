# This factory is not the same as the others, and doesn't use
# django-factories but it mimics their functionality...

from odk_logger.models import XForm, Instance
import os
from datetime import datetime, timedelta

from pyxform import *
from pyxform.builder import create_survey_element_from_dict

XFORM_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000"
ONE_HOUR = timedelta(0, 3600)

def _load_registration_survey_object():
    """
    Loads a registration survey with all the values necessary
    to register a surveyor.
    """
    survey = Survey(name=u"registration", id_string=u"registration")
    survey.add_child(create_survey_element_from_dict({
        u'type':u'text',u'name':u'name', u'label':u'Name'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'start time',
        u'name': u'start'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'end time',
        u'name': u'end'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'imei',
        u'name': u'device_id'
    }))
    return survey

def _load_simple_survey_object():
    """
    Returns a "watersimple" survey object,
    complete with questions.
    """
    survey = Survey(name=u"WaterSimple", id_string=u"WaterSimple")
    survey.add_child(create_survey_element_from_dict({
        u'hint': {u'English':u'What is this point named?'},
        u'label': {u'English':u'Water Point Name'},
        u'type': u'text',
        u'name': u'name'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'hint': {u'English':u'How many people use this every month?'},
        u'label': {u'English':u'Monthly Usage'},
        u'name': u'users_per_month',
        u'type': u'integer'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'gps',
        u'name': u'geopoint',
        u'label': {u'English':u'Location'}
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'imei',
        u'name': u'device_id'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'start time',
        u'name': u'start'
    }))
    survey.add_child(create_survey_element_from_dict({
        u'type': u'end time',
        u'name': u'end'
    }))
    return survey


class XFormManagerFactory(object):

    def create_registration_xform(self):
        """
        Calls 'get_registration_xform', saves the result, and returns.
        """
        xf = self.get_registration_xform()
        xf.save()
        return xf

    def get_registration_xform(self):
        """
        Gets a registration xform. (currently loaded in from fixture)
        Returns it without saving.
        """
        reg_xform = _load_registration_survey_object()
        return XForm(xml=reg_xform.to_xml())

    def create_registration_instance(self, custom_values={}):
        i = self.get_registration_instance(custom_values)
        i.save()
        return i

    def get_registration_instance(self, custom_values={}):
        """
        1. Checks to see if the registration form has been created alread. If not, it loads it in.
        
        2. Loads a registration instance.
        """
        registration_xforms = XForm.objects.filter(title=u"registration")
        if registration_xforms.count() == 0:
            xf = self.create_registration_xform()
        else:
            xf = registration_xforms[0]
        
        values = {
            u'device_id': u'12345',
            u'start': u'2011-01-01T09:50:06.966',
            u'end': u'2011-01-01T09:53:22.965'
        }
        
        if u'start' in custom_values:
            st = custom_values[u'start']
            custom_values[u'start'] = st.strftime(XFORM_TIME_FORMAT)

            #if no end_time is specified, defaults to 1 hour
            values[u'end'] = (st+ONE_HOUR).strftime(XFORM_TIME_FORMAT)
        
        if u'end' in custom_values:
            custom_values[u'end'] = custom_values[u'end'].strftime(XFORM_TIME_FORMAT)
        
        values.update(custom_values)
        
        reg_xform = _load_registration_survey_object()
        reg_instance = reg_xform.instantiate()
        reg_instance._id = xf.id_string
        
        for k, v in values.items():
            reg_instance.answer(name=k, value=v)
        
        instance_xml = reg_instance.to_xml()
        
        return Instance(xml=instance_xml)
    
    def create_simple_xform(self):
        xf = self.get_simple_xform()
        xf.save()
        return xf
    
    def get_simple_xform(self):
        survey_object = _load_simple_survey_object()
        return XForm(xml=survey_object.to_xml())
    
    def create_simple_instance(self, custom_values={}):
        i = self.get_simple_instance(custom_values)
        i.save()
        return i
    
    def get_simple_instance(self, custom_values={}):
        simple_xforms = XForm.objects.filter(title=u"WaterSimple")
        if simple_xforms.count() == 0:
            xf = self.create_simple_xform()
        else:
            xf = simple_xforms[0]
        
        #these values can be overridden with custom values
        values = {
            u'device_id': u'12345',
            u'start': u'2011-01-01T09:50:06.966',
            u'end': u'2011-01-01T09:53:22.965',
            u'geopoint': u'40.783594633609184 -73.96436698913574 300.0 4.0'
        }
        
        if u'start' in custom_values:
            st = custom_values[u'start']
            custom_values[u'start'] = st.strftime(XFORM_TIME_FORMAT)

            #if no end_time is specified, defaults to 1 hour
            values[u'end'] = (st+ONE_HOUR).strftime(XFORM_TIME_FORMAT)
        
        if u'end' in custom_values:
            custom_values[u'end'] = custom_values[u'end'].strftime(XFORM_TIME_FORMAT)
        
        values.update(custom_values)
        
        water_simple_survey = _load_simple_survey_object()
        simple_survey = water_simple_survey.instantiate()
        
        for k, v in values.items():
            simple_survey.answer(name=k, value=v)
        
        #setting the id_string so that it doesn't end up
        #with the timestamp of the new survey object
        simple_survey._id = xf.id_string
        
        instance_xml = simple_survey.to_xml()
        
        return Instance(xml=instance_xml)

