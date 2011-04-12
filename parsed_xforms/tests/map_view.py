from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from nga_districts.models import Zone, State, LGA
from xform_manager.models import Instance
from parsed_xforms.models import ParsedInstance
from parsed_xforms.views import map_data_points
import re, json

class TestMapView(TestCase):
    
    def setUp(self):
        self.zone_slug = 'southeast'
        self.state_slug = 'anambra'
        self.lga_slug = 'awka_north'
        self.zone, created = Zone.objects.get_or_create(
            name="Southeast", slug="southeast")
        self.state, created = State.objects.get_or_create(
            zone=self.zone, name="Anambra", slug="anambra")
        self.lga, created = LGA.objects.get_or_create(
            state=self.state, name="Awka North", slug=self.lga_slug)

        self.instance = Instance.objects.create(xml=u'<?xml version=\'1.0\' ?><Water id="Water_2011_03_18"><imei>356221036381384</imei><start_time>2011-03-22T17:32:49.472</start_time><end_time>2011-03-22T17:34:36.472</end_time><research_assistant_name>Andrew</research_assistant_name><photo>1300811590326.jpg</photo><location><gps>9.055572152137756 7.51838743686676 558.0 6.0</gps><zone>southeast</zone><state_in_southeast>anambra</state_in_southeast><lga_in_anambra>awka_north</lga_in_anambra><ward>FAKE</ward><community>FAKE</community></location><locality>FAKE</locality><nearest_school_or_clinic>FAKE</nearest_school_or_clinic><pre_existing_id>FAKE</pre_existing_id><type>borehole</type><distribution_type>single_point</distribution_type><lift_mechanism>diesel</lift_mechanism><developed_by>federal_government</developed_by><managed_by>federal_government</managed_by><managing_organizations><federal_government><organization_name>FAKE</organization_name></federal_government><state_government /><local_government /><community /><individual /><international_development_partner /><private_organization /></managing_organizations><pay_for_water>yes</pay_for_water><used_today>yes</used_today><physical_state>newly_constructed</physical_state><other_close_water>yes</other_close_water><times_used>year_round</times_used><help_completed>nobody</help_completed><thank_you /></Water>')
        self.parsed_instance = ParsedInstance.objects.get(instance=self.instance)
        self.lga = self.parsed_instance.lga


    def tearDown(self):
        self.instance.delete()
    
    def test_lga_gets_assigned_properly(self):
        self.assertEqual(self.lga.slug, u"awka_north")
        self.assertEqual(self.lga.state.slug, u"anambra")

    def test_map_view(self):
        url = reverse(map_data_points, kwargs={'lga_id' : self.lga.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        response_str = str(response)
        header = """Vary: Cookie
Content-Type: text/html; charset=utf-8

"""
        self.assertTrue(response_str.startswith(header))
        json_response = response_str[len(header):]
        j = json.loads(json_response)
        
        #assert that the factory-created survey shows up in the json
        #sent to the view
        self.assertTrue(len(j)==1)
