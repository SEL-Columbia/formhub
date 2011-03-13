from django.db import models
import re

def sluggify(s):
    result = s.lower()
    return re.sub("[^a-z]+", "_", result)

class NamedModel(models.Model):
    name = models.TextField()
    slug = models.SlugField()

    def save(self, *args, **kwargs):
        print self.name
        self.slug = sluggify(self.name)
        super(NamedModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Zone(NamedModel):
    @classmethod
    def get_phase2_query_set(cls):
        return cls.objects.filter(name__in=[u"Northwest", u"Southeast"])


class State(NamedModel):
    zone = models.ForeignKey(Zone, related_name="states")

    @classmethod
    def get_phase2_query_set(cls):
        return cls.objects.filter(zone__in=Zone.get_phase2_query_set())


class LGA(NamedModel):
    state = models.ForeignKey(State, related_name="lgas")
    scale_up = models.BooleanField()
    unique_slug = models.TextField(null=True)
    afr_id = models.TextField(null=True)
    kml_id = models.TextField(null=True)
    latlng_str = models.TextField(null=True)

    @classmethod
    def get_phase1_lga_names(cls):
        return [u"Nwangele", u"Miga", u"Song", u"Kuje", u"Akoko North West"]

    @classmethod
    def get_phase1_query_set(cls):
        return cls.objects.filter(name__in=cls.get_phase1_lga_names())

    @classmethod
    def get_phase2_query_set(cls):
        return cls.objects.filter(
            state__in=State.get_phase2_query_set(),
            scale_up=True,
            ).exclude(name__in=cls.get_phase1_lga_names())
