# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
import re


def sluggify(s):
    result = s.lower()
    return re.sub("[^a-z]+", "_", result)


class NamedModel(models.Model):
    name = models.TextField()
    slug = models.SlugField()

    def save(self, *args, **kwargs):
        self.slug = sluggify(self.name)
        super(NamedModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Zone(NamedModel):
    @classmethod
    def get_phase2_query_set(cls):
        return cls.objects.filter(name__in=[u"Northwest", u"Southeast"])

    @classmethod
    def get_query_set_for_round(cls, r):
        result = cls.objects.filter(states__lgas__survey_round=r)
        result = result.distinct()
        result = result.order_by("name")
        return result


class State(NamedModel):
    zone = models.ForeignKey(Zone, related_name="states")

    @classmethod
    def get_phase2_query_set(cls):
        return cls.objects.filter(zone__in=Zone.get_phase2_query_set())

    @classmethod
    def get_query_set_for_round(cls, r):
        result = cls.objects.filter(lgas__survey_round=r)
        result = result.distinct()
        result = result.order_by("name")
        return result


class LGA(NamedModel):
    state = models.ForeignKey(State, related_name="lgas")
    scale_up = models.BooleanField()
    unique_slug = models.TextField(null=True)
    afr_id = models.TextField(null=True)
    kml_id = models.TextField(null=True)
    latlng_str = models.TextField(null=True)
    survey_round = models.IntegerField(default=0)
    included_in_malaria_survey = models.BooleanField(default=False)

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

    @classmethod
    def get_ordered_phase2_query_set(cls):
        return cls.get_phase2_query_set().order_by(
            "state__zone__name",
            "state__name",
            "name"
            )

    @classmethod
    def set_survey_round_field(cls):
        round1 = cls.get_phase1_query_set()
        round1.update(survey_round=1)
        round2 = cls.get_phase2_query_set()
        round2.update(survey_round=2)
        round3 = cls.objects.filter(scale_up=True, survey_round=0)
        round3.update(survey_round=3)

    @classmethod
    def get_query_set_for_round(cls, r):
        return cls.objects.filter(survey_round=r).order_by("name")
