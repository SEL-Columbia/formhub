# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.template.loader import render_to_string
from django.template.defaultfilters import slugify

from pyxform.builder import create_survey_from_xls
from odk_logger.models import XForm
from odk_viewer.models import DataDictionary

import urllib2
import re


class QuickConverter(forms.Form):
    xls_file = forms.FileField(label="XLS File")

    def get_survey(self):
        if self.is_valid():
            xls = self.cleaned_data['xls_file']
            return create_survey_from_xls(xls)


@login_required
def dashboard(request):
    context = RequestContext(request)
    context.form = QuickConverter()
    context.odk_url = request.build_absolute_uri("/%s" % request.user.username)

    if request.method == 'POST':
        try:
            form = QuickConverter(request.POST, request.FILES)
            survey = form.get_survey()
            publish(request.user, survey)
            context.message = {
                'type': 'success',
                'text': 'Successfully published %s.' % survey.id_string,
                }
        except Exception as e:
            context.message = {
                'type': 'error',
                'text': unicode(e),
                }

    return render_to_response("dashboard.html", context_instance=context)


def publish(user, survey):
    kwargs = {
        'xml': survey.to_xml(),
        'downloadable': True,
        'user': user,
        }
    xform = XForm.objects.create(**kwargs)

    # need to also make a data dictionary
    kwargs = {
        'xform': xform,
        'json': survey.to_json(),
        }
    data_dictionary = DataDictionary.objects.create(**kwargs)


def tutorial(request):
    context = RequestContext(request)
    context.template = 'tutorial.html'
    username = request.user.username if request.user.username else \
        'your-user-name'
    context.odk_url = request.build_absolute_uri("/%s" % username)
    return render_to_response('base.html', context_instance=context)


class GoogleDocSection(dict):

    FIELDS = ['level', 'id', 'title', 'content']

    def to_html(self):
        return render_to_string('section.html', self)


class TreeNode(list):

    def __init__(self, value=None, parent=None):
        self.value = value
        self.parent = parent
        list.__init__(self)

    def add_child(self, value):
        child = TreeNode(value, self)
        self.append(child)
        return child


class GoogleDoc(object):

    def __init__(self, url):
        f = urllib2.urlopen(url)
        self._html = f.read()
        f.close()
        self._extract_content()
        self._extract_sections()

    def _extract_content(self):
        m = re.search(r'<body>(.*)</div><div id="footer">', self._html, re.DOTALL)
        self._content = m.group(1)
        self._fix_image_url()

    def _fix_image_url(self):
        def repl(m):
            # we have to make the url for this image absolute
            return re.sub('src="', 'src="https://docs.google.com/document/', m.group(1))

        self._content = re.sub(r'(<img[^>]*>)', repl, self._content)

    def _extract_sections(self):
        self._sections = []
        header = r'<h(?P<level>\d) class="c\d"><a name="(?P<id>[^"]+)"></a><span>(?P<title>[^<]+)</span></h\d>'
        l = re.split(header, self._content)
        print len(l)
        l.pop(0)
        while l:
            section = GoogleDocSection(
                # hack: cause we started with h3 in google docs
                level=int(l.pop(0)) - 2,
                id=l.pop(0),
                title=l.pop(0),
                content=l.pop(0),
                )
            section['id'] = slugify(section['title'])
            self._sections.append(section)

    def _construct_section_tree(self):
        self._section_tree = TreeNode(GoogleDocSection(level=0))
        current_node = self._section_tree
        for section in self._sections:
            while section['level'] <= current_node.value['level']:
                current_node = current_node.parent
            while section['level'] > current_node.value['level'] + 1:
                current_node = current_node.add_child(GoogleDocSection(level=current_node.value['level'] + 1))
            assert section['level'] == current_node.value['level'] + 1
            current_node = current_node.add_child(section)

    def _navigation_list(self, node=None):
        if node is None:
            self._construct_section_tree()
            return self._navigation_list(self._section_tree)
        result = ""
        if 'title' in node.value and 'id' in node.value:
            result += '<li><a href="#%(id)s">%(title)s</a></li>' % node.value
        if len(node) > 0:
            result += "<ul>%s</ul>" % "\n".join([self._navigation_list(child) for child in node])
        return result

    def _navigation_html(self):
        return render_to_string('section.html', {
                'level': 1,
                'id': 'contents',
                'title': 'Contents',
                'content': self._navigation_list(),
                })

    def to_html(self):
        return """
<div class="row">
  <div class="span12">%(content)s</div>
  <div class="span4">%(nav)s</div>
</div>
""" % {
            'nav': self._navigation_html(),
            'content': '\n'.join([s.to_html() for s in self._sections]),
            }


def syntax(request):
    url = 'https://docs.google.com/document/pub?id=1Dze4IZGr0IoIFuFAI_ohKR5mYUt4IAn5Y-uCJmnv1FQ'
    doc = GoogleDoc(url)
    context = RequestContext(request)
    context.content = doc.to_html()
    return render_to_response('base.html', context_instance=context)
