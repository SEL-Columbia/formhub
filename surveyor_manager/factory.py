#factories can be git-downloaded and installed from here:
#https://github.com/mirhampt/django-factories

from factories import Factory, blueprint

FIRST_NAMES = ["Alan", "Bob", "Charlie", "Dingo", "Ellen", "Fiona", "Gilbert", "Hewitt", "Ingrid", "Justin", "Keith", "Lawrence", "Mangrove"]
MIDDLE_NAMES = ["Alex", "Bowie", "Chuck", "Dood", "Evelyn", "Farley", "Gabriella", "Howard"]
LAST_NAMES = ["Arlington", "Billsworth", "ChileanMiner", "Dorothy", "Elephant", "Farthingtonsworth", "Gillette", "Hildason", "Inkscape", "Janevich", "Klaus-Schlinger", "Lapdog"]

import random, re

def random_name(name_type):
    name_list = []
    if name_type == "first":
        name_list = FIRST_NAMES
    elif name_type == "middle":
        name_list = MIDDLE_NAMES
    else:
        name_list = LAST_NAMES
    return name_list[random.randint(0, len(name_list)-1)]

def random_full_name():
    return "%s %s %s" % (random_name("first"), random_name("middle"), random_name("last"))

class SurveyorManagerFactory(Factory):
    "Factory for surveyor manager application."

    @blueprint(model='surveyor_manager.Surveyor')
    def surveyor(self):
        "A simple surveyor with a name."
        first_name = "%s %s" % (random_name("first"), random_name("middle"))
        last_name = random_name("last")
        name = "%s %s" % (first_name, last_name)
        username = re.sub("\s", "_", name).lower()
        return {
            'first_name': first_name,
            'last_name': last_name,
            'name': name,
            'username': username
        }
    
    
    @blueprint(model='surveyor_manager.Surveyor')
    def staff(self):
        "a simple staff member"
        member = self.surveyor()
        member['is_staff'] = True
        return member
    
    @blueprint(model='surveyor_manager.Surveyor')
    def admin(self):
        "a simple admin"
        member = self.surveyor()
        member['is_admin'] = True
        return member

