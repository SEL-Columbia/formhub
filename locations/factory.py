#factories can be git-downloaded and installed from here:
#https://github.com/mirhampt/django-factories

from factories import Factory, blueprint
from treebeard.mp_tree import MP_Node

from locations.models import District
from django.forms.models import model_to_dict

import random

def get_root_district():
    root_node = District.get_first_root_node()
    if root_node is None:
        root_node = District.add_root(name="New York World", \
                    latlng_string="40.77,73.98",
                    kml_present=False, active=False)
    return root_node


STATE_PREFIX = ["New", "Old", "El", "Le", "The", "Inner", "Outer", "Sub", "Super"]
STATE_NAMES = ["Jersey", "Joysey", "Akoko", "York", "Paris", "Amsterdam", "Belleville", "Amnityville", \
                    "Chicago", "FroyoVille", "Burma", "China", "Russia", "Nigeria", "Atlantis"]
COMPASS_DIRECTIONS = ["North", "South", "East", "West", "North-West", "North-East", \
                "South-West", "South-East"]

def random_district_name_of_type(type):
    selection_list = []
    if type=="prefix":
        selection_list = STATE_PREFIX
    elif type=="name":
        selection_list = STATE_NAMES
    else:
        selection_list = COMPASS_DIRECTIONS
    return selection_list[random.randint(0, len(selection_list)-1)]

def random_district_name():
    return "%s %s %s" % (random_district_name_of_type("prefix"), random_district_name_of_type("name"), \
                            random_district_name_of_type("compass"))

class DistrictFactory(Factory):
    "Factory for locations application."
    
    @blueprint(model='locations.District')
    def district(self):
        """
        A district is stored hierarchichally and treebeard is
        not nice with inserting things in so somethign special
        had to be done to make this possible.
        """
        name = random_district_name()
        root_node = get_root_district()
        newobj = root_node.add_child(name=name, kml_present=False, active=False)
        new_dict = model_to_dict(newobj)
        newobj.delete()
        #annoying, but root_node forgets about its kids
        root_node.numchild = root_node.numchild+1
        root_node.save()
        
        return new_dict
        
    @blueprint(model='locations.District')
    def active_district(self):
        "district is marked active"
        dist = self.district()
        dist['active']=True
        return dist
