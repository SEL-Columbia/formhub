# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.template.loader import render_to_string

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
    context.odk_url = request.build_absolute_uri(request.user.username)

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
    context.odk_url = request.build_absolute_uri(username)
    return render_to_response('base.html', context_instance=context)


def syntax(request):

    def html():
        url = 'https://docs.google.com/document/pub?id=1Dze4IZGr0IoIFuFAI_ohKR5mYUt4IAn5Y-uCJmnv1FQ'
        f = urllib2.urlopen(url)
        result = f.read()
        f.close()
        return result

    def content():
        m = re.search(r'<body>(.*)<div id="footer">', html(), re.DOTALL)
        return m.group(1)

    def wrap_sections():
        header = r'<h(?P<level>\d) class="c\d"><a name="(?P<id>[^"]+)"></a><span>(?P<title>[^<]+)</span></h\d>'
        l = re.split(header, content())
        l.pop(0)
        result = ''
        while l:
            d = {
                # hack: cause we started with h3 in google docs
                'level': int(l.pop(0)) - 2,
                'id': l.pop(0),
                'title': l.pop(0),
                'content': l.pop(0),
                }
            result += render_to_string('section.html', d)
        return result

    def fix_image_url(html):
        # this isn't working because an ampersand in the url is being
        # escaped, gahh.
        return re.sub(
            'src="pubimage\?',
            'ref="https://docs.google.com/document/pubimage?',
            html
            )

    context = RequestContext(request)
    context.content = fix_image_url(wrap_sections())
    return render_to_response('base.html', context_instance=context)
