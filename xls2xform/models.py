from django.db import models
from django.contrib.auth.models import User
import json
import copy
import os
import re
import pyxform

class SectionIncludeError(Exception):
    def __init__(self, container, include_slug):
        self.container = container
        self.include_slug = include_slug

class IncludeNotFound(SectionIncludeError):
    def __repr__(self):
        return "The section '%s' was not able to include the section '%s'" % \
                    (self.container, self.include_slug)
    
class CircularInclude(SectionIncludeError):
    def __repr__(self):
        return "The section '%s' detected a circular include of section '%s'" % \
                    (self.container, self.include_slug)

class XForm(models.Model):
    #id_string should definitely be changed to "name".
    id_string = models.CharField(max_length=32)
    title = models.CharField(max_length=32)
    latest_version = models.ForeignKey('XFormVersion', null=True, related_name="active_xform")
    user = models.ForeignKey(User, related_name="xforms")
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    def __init__(self, *args, **kwargs):
        sections = kwargs.pop(u'sections', [])
        super(XForm, self).__init__(*args, **kwargs)
        
    def __unicode__(self):
        return "[%s]: %s" % (self.id_string, self.title)
    
    def save(self, *args, **kwargs):
        super(XForm, self).save(*args, **kwargs)
        if self.latest_version is None:
            self.latest_version = XFormVersion.objects.create(xform=self, version_number=0)
            self.save()
    
    def export_survey(self, finalize=True, debug=False):
        """
        the first way of exporting surveys didn't allow imports
        (without writing temp files, which is hacky.)

        so i think it's best to go a different route--

        1. have this django app gather all the includes (from the portfolio)
            -- this allows us to display what includes are missing and prompt
               for them before creating the survey
        2. this django app will then send a "packaged" dict to pyxform which
           can be used to render the survey.
            -- the packaged dict contains 4 things
                * name (the survey name, no datestamp)
                * id_string (for possible later reference)
                * questions_list (with hierarchy of groups, etc.)
                * question_types (for maximum customizability,
                                  language compaitibility, etc.)
        """
        survey_package = self._create_survey_package()
        if debug:
            return survey_package
        return pyxform.create_survey(**survey_package)

    def _create_survey_package(self):
        """
        since the base_section is the "main" section, we want to remove it from the
        "sections" being included.
        """
        included_sections = self.latest_version.section_pyobjs_by_slug()
        included_sections.pop('_base')
        return {
            'title': re.sub(" ", "_", self.title),
            'id_string': self.latest_version.get_unique_id(),
            'main_section': self.latest_version.base_section.questions_list,
            'sections': included_sections,
#            'question_type_dictionary':
#            self.latest_version.get_question_type_dictionary(),
        }
    
    def add_or_update_section(self, *args, **kwargs):
        """
        Automatically creates a new version whenever updating one of
        the sections.
        """
        slug = kwargs.get(u'slug')
        
        lv = self.latest_version
        slug_dict = lv.sections_by_slug()
        new_section = XFormSection(*args, **kwargs)
        
        if slug in slug_dict.keys():
            #TODO: check to see if the new section contains changes
            #assuming not--
            remove_section = slug_dict[slug]
        else:
            remove_section = None
        
        nv = lv._clone()
        nv.sections.remove(remove_section)
        
        new_section.save()
        nv.sections.add(new_section)
        
        self.latest_version = nv
        self.save()
        return nv
    
    def remove_section(self, *args, **kwargs):
        slug = kwargs.get(u'slug', None)
        lv = self.latest_version
        matching_section = lv.sections.get(slug=slug)
        if matching_section is None: return lv
        
        slugs = lv.base_section_slugs()
        if slug in slugs:
            #when the slug is active, we need to
            #remove it from 2 lists
            slugs.remove(slug)
            nv = self.order_base_sections(slugs)
            nv.sections.remove(matching_section)
        else:
            nv = lv._clone()
            nv.sections.remove(matching_section)
            self.latest_version = nv
            self.save()

    def activate_section(self, section):
        """
        Adds this section to the "base_section".
        """
        section_slug = section.slug
        slugs = self.latest_version.base_section_slugs()
        if section_slug not in slugs:
            slugs.append(section_slug)
            self.order_base_sections(slugs)
        return self.latest_version

    def deactivate_section(self, section):
        """
        Removes this section from the "base_section".
        """
        section_slug = section.slug
        slugs = self.latest_version.base_section_slugs()
        if section_slug in slugs:
            slugs.remove(section_slug)
            self.order_base_sections(slugs)
    
    @property
    def finalized_version_count(self):
        return self.versions.exclude(id_stamp='').count()
    
    def order_base_sections(self, slug_list):
        """
        This sets the order of the sections included in the base_section.
        This will automatically handle "activation" of all the sections.
        """
        v = self.latest_version._clone()
        new_base = v.base_section
        slug_list_includes = []
        for slug in slug_list:
            slug_list_includes.append({u'type': u'include', u'name': slug})
        full_survey = {
            u'type': u'survey',
            u'name': self.latest_version.base_section.slug,
            u'children' : slug_list_includes
            }
        new_base.section_json = json.dumps(full_survey)
        new_base.save()
        v.save()
        self.latest_version = v
        self.save()
        return v

class XFormVersion(models.Model):
    xform = models.ForeignKey(XForm, related_name="versions")
    date_created = models.DateTimeField(auto_now_add=True)
    
    base_section = models.ForeignKey('XFormSection', null=True, related_name="bversions")
    qtypes_section = models.ForeignKey('XFormSection', null=True, related_name="qversions")
    id_stamp = models.CharField(max_length=64)
    
    version_number = models.IntegerField()
    
    _included_sections = None
    
    def __init__(self, *args, **kwargs):
        #this even creates a new base_section when the value doesn't change.
        empty_base_survey = {
            u'type': 'survey',
            u'name': u'',
            u'children': []
            }
        empty_base_survey_str = json.dumps(empty_base_survey)
        base_section_json = kwargs.pop(u'base_section_json',
                                       empty_base_survey_str)
        base_section = XFormSection.objects.create(section_json=base_section_json, slug="_base")
        kwargs[u'base_section'] = base_section
        
        #not sure if this is the best way to do this... but it works for now.
        # qtypes_json = kwargs.pop(u'qtypes_section_json', u'null')
        # qtypes_section = XFormSection.objects.create(section_json=qtypes_json, slug="_qtypes")
        # kwargs[u'qtypes_section'] = qtypes_section

        super(XFormVersion, self).__init__(*args, **kwargs)
    
    def _clone(self):
        bsj = self.base_section.section_json
        vn = self.version_number
        new_version = XFormVersion.objects.create(base_section_json=bsj, xform=self.xform, version_number=vn+1)
        for s in self.sections.all(): new_version.sections.add(s)
        return new_version
    
    #XFormVersion.sections_by_slug --is it used?
    
    def get_question_type_dictionary(self):
        return self.qtypes_section.questions_list
    
    def get_unique_id(self):
        """
        it would be awesome to have the ability to look up surveys
        by their unique id stamps.
        
        also, a null id_stamp is a good indication that the version
        can be purged.
        """
        def base36encode(num, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'):
            #Using base36 encode to have a character (or 2) at the end
            # of the xforms id_string that signifies the version number
            # this way, xforms exported on the same day do not have the
            # same ID string.
            if num == 0:
                return alphabet[0]
            base36 = ''
            while num != 0:
                num, i = divmod(num, len(alphabet))
                base36 = alphabet[i] + base36
            return base36
        
        if self.id_stamp in [None, u'']:
            #creates format: "xform_2011_01_01a"
            import datetime
            self.id_stamp = "%s_%s%s" % (
                    self.xform.id_string,
                    datetime.date.today().strftime("%Y_%m_%d"),
                    base36encode(self.xform.finalized_version_count)
                )
            self.save()
        return self.id_stamp
    
    def sections_by_slug(self):
        sections = {}
        for s in self.sections.all(): sections[s.slug] = s
        # why isn't the base section in sections.all()
        sections[self.base_section.slug] = self.base_section
        return sections

    def section_pyobjs_by_slug(self):
        sections = self.sections_by_slug()
        for k, v in sections.items():
            sections[k] = json.loads(v.section_json)
        return sections
    
    def base_section_slugs(self):
        base_section_json = self.base_section.section_json 
        j_arr = json.loads(base_section_json)[u'children']
        slugs = []
        for j in j_arr:
            s = j.get(u'type', None)
            if s == 'include':
                include_slug = j.get(u'name')
                slugs.append(include_slug)
        return slugs

    def get_base_section_name(self):
        return self.base_section.slug
    
    def included_base_sections(self):
        if self._included_sections is None:
            section_includes = json.loads(self.base_section.section_json)
            sections = []
            for incl in self.base_section_slugs():
                sections.append(self.sections.get(slug=incl))
            self._included_sections = sections
        return self._included_sections
    
    def all_sections(self):
        included_sections = self.included_base_sections()
        available_section_list = list(self.sections.all())
        for s in available_section_list: s.is_marked_included = s in self._included_sections
        return (available_section_list, self._included_sections)


class XFormSection(models.Model):
    slug = models.TextField()
    section_json = models.TextField()
    versions = models.ManyToManyField("XFormVersion", related_name="sections")
    is_marked_included = False
    _sub_sections = None

    def __init__(self, *args, **kwargs):
        """
        converts a section_dict argument to json.
        """
        slug = kwargs.get(u'slug')
        d = kwargs.pop(u'section_dict', kwargs.pop('section_dict', None))
        if type(d) == list:
            #if a list, then wrap in an empty survey
            d = {
                u'type': 'survey',
                u'name': slug,
                u'children': d
                }
        
        if d is not None:
            kwargs[u'section_json'] = json.dumps(d)
        return super(XFormSection, self).__init__(*args, **kwargs)

    def sub_sections(self):
        def traverse_pyobj(pyobj):
            if type(pyobj)==dict:
                if pyobj.get(u'type')==u'include':
                    yield pyobj[u'name']
                for include in traverse_pyobj(pyobj.get(u'children')):
                    yield include
            if type(pyobj)==list:
                for element in pyobj:
                    for include in traverse_pyobj(element):
                        yield include
        
        if self._sub_sections is None:
            sd = json.loads(self.section_json)
            self._sub_sections = list(traverse_pyobj(sd))
        return self._sub_sections
    
    @property
    def questions_list(self):
        surv = json.loads(self.section_json)
        if type(surv) == list:
            qs = surv
        elif surv is None:
            qs = None
        else:
            qs = surv[u'children']
        return qs
