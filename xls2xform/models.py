from django.db import models
from django.contrib.auth.models import User
import json
import copy
import os
import re

import pyxform

from xls2xform import section_adjuster
from xls2xform import pyxform_include_packager
from xls2xform_errors import SectionIncludeError, IncludeNotFound, CircularInclude

class Survey(models.Model):
    root_name = models.CharField(max_length=32)
    title = models.CharField(max_length=32)
    user = models.ForeignKey(User, related_name="surveys", null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    # i don't know why, but base_section was having a clash and needs a related name
    base_section = models.ForeignKey('SurveySection', null=True, related_name="related_survey")
    version_count = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return "[%s]: %s" % (self.root_name, self.title)

    @property
    def _section_slugs(self):
        """
        Returns a list of all the sections available for this survey.
        """
        return sorted([s[u'slug'] for s in self.survey_sections.all().values(u'slug')])

    @property
    def _sections_data_by_slug(self):
        ssbs = dict([(s.slug, s._children) for s in self.survey_sections.all()])
        return (ssbs.pop('_base'), ssbs)

    @property
    def _sections(self):
        return self.survey_sections

    @property
    def _base_section(self):
        # If there is no base_section, we want to add an empty one.
        if self.base_section == None:
            self.base_section = SurveySection.objects.create(slug="_base", children_json="[]", survey=self)
            self.save()
        return self.base_section

    @property
    def _unique_id(self):
        # returns a unique id from the version
        return "%s_%d" % (self.root_name, self.finalized_version_count)

    def _survey_package(self):
        main_section = self.base_section._children
        available_sections = dict([[s.slug, s._children]
                                for s in self._sections.exclude(slug="_base").all()])
        return { 'main_section': main_section,
                    'title': self.title,
                    'root_name': self._unique_id,
                    'sections': available_sections }

    def add_or_update_section(self, *args, **kwargs):
        slug = kwargs[u'slug']
        try:
            section = self._sections.get(slug=slug)
            section.children_json = kwargs[u'children_json']
            section.save()
        except SurveySection.DoesNotExist:
            kwargs[u'survey'] = self
            section = SurveySection.objects.create(**kwargs)

    @property
    def finalized_version_count(self):
        # a simple way to do version counts...
        self.version_count += 1
        self.save()
        return self.version_count

class SurveySection(models.Model):
    slug = models.TextField()
    children_json = models.TextField(default="[]")
    survey = models.ForeignKey("Survey", related_name="survey_sections")

    def make_adjustment(self, base, action):
        """
        section.make_adjustment only works in certain circumstances
        (eg. when reordering the _base section).
        """
        base_sections = base._children
        selfs_include = {u'type':u'include',u'name':self.slug}
        new_sections = section_adjuster.make_adjustment(base_sections, selfs_include, action)
        base.children_json = json.dumps(new_sections)
        base.save()
        if action == "delete":
            self.delete()

    @property
    def _children(self):
        """
        This returns a list of the children of this section, and is used a lot.
        """
        return json.loads(self.children_json)

    @property
    def includes_list(self):
        """
        Returns a list of slugs of included sections. Used in UI and tests.
        """
        return [cd[u'name'] for cd in self._children if cd[u'type']==u'include']
