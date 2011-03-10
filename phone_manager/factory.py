#factories can be git-downloaded and installed from here:
#https://github.com/mirhampt/django-factories

from factories import Factory, blueprint

import random

class PhoneManagerFactory(Factory):
    "Factory for phone manager application."

    @blueprint(model='phone_manager.Phone')
    def phone(self):
        "A simple phone."
        
        imei = random.randint(1000000, 9999999)
        visible_id = random.randint(100, 9999)
        phone_number = "%s" % random.randint(0,20) #could be a repeat
        
        return {
            "status": "functional", 
            "phone_number": str(phone_number), 
            "note": "",
            "surveyor_id": 2, 
            "visible_id": str(visible_id),
            "imei": str(imei)
        }
