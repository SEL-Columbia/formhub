from django.db import models
from parsed_instance import ParsedInstance
from surveyor_manager.models import Surveyor
from common_tags import NAME, REGISTRATION

class Registration(models.Model):
    parsed_instance = models.ForeignKey(ParsedInstance)
    surveyor = models.ForeignKey(Surveyor)

    class Meta:
        app_label = "parsed_xforms"

    @classmethod
    def get_registered_surveyor(cls, parsed_instance):
        # We need both a phone and a start time to know who this
        # survey should be attributed to.
        if parsed_instance.phone is None or \
                parsed_instance.start_time is None:
            return None
        # Find all registrations for this phone that happened before
        # this instance.
        qs = cls.objects.filter(
            parsed_instance__phone=parsed_instance.phone,
            parsed_instance__start_time__lte=parsed_instance.start_time
            )
        # Order them by start time.
        qs = qs.order_by("-parsed_instance__start_time")
        if qs.count()==0:
            return None
        most_recent_registration = qs[0]
        return most_recent_registration.parsed_instance.surveyor

    def _create_surveyor(self):
        name = self.parsed_instance.instance.get(NAME)
        if not name:
            raise Exception(
                "Name must be nonempty.",
                self.parsed_instance.instance.xml
                )
        # todo: come up with a better username and password
        kwargs = {"username" : name,
                  "name" : name,
                  "password" : "noneisabadd3f4u1tpassword"}
        surveyor, created = Surveyor.objects.get_or_create(**kwargs)
        return surveyor

    def save(self, *args, **kwargs):
        self.surveyor = self._create_surveyor()
        super(Registration, self).save(*args, **kwargs)


def _set_surveyor(sender, **kwargs):
    # We need to check that this is a new ParsedInstance so we don't
    # enter an infinite loop up setting the surveyor, saving, looking
    # at this saved ParsedInstance, setting the surveyor, saving, ...
    if kwargs["created"]:
        parsed_instance = kwargs["instance"]
        root_node_name = parsed_instance.instance.get_root_node_name()
        if root_node_name.lower()==REGISTRATION.lower():
            registration, created = Registration.objects.get_or_create(
                parsed_instance=parsed_instance)
            parsed_instance.surveyor = registration.surveyor
        else:
            parsed_instance.surveyor = \
                Registration.get_registered_surveyor(parsed_instance)
        parsed_instance.save()

from django.db.models.signals import post_save
post_save.connect(_set_surveyor, sender=ParsedInstance)
