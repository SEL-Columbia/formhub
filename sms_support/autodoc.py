#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" SMS Support Automatic Documentation (Web View)

    Provides the get_autodoc_for(xform) function.
    It is used inside the main.views.show() view to display
    an HTML documentation about how to fill the SMS for that form.

    Output is HTML ; not raw. Output uses only span markup with classes
    so it should be somewhat easy to restyle """

import json
import datetime

from tools import (DEFAULT_SEPARATOR, DEFAULT_ALLOW_MEDIA, MEDIA_TYPES,
                   DEFAULT_DATE_FORMAT, DEFAULT_DATETIME_FORMAT)


def get_sample_data_for(question, json_survey, as_names=False):

    """ return an example data for a particular question.

        If as_names is True, returns name (not sms_field) of the question """

    xlsf_name = question.get('name')
    xlsf_type = question.get('type')
    xlsf_choices = question.get('children')
    now = datetime.datetime.now()
    xlsf_date_fmt = json_survey.get('sms_date_format', DEFAULT_DATE_FORMAT) \
        or DEFAULT_DATE_FORMAT
    xlsf_datetime_fmt = json_survey.get('sms_date_format',
                                        DEFAULT_DATETIME_FORMAT) \
        or DEFAULT_DATETIME_FORMAT

    def safe_wrap(value):
        return unicode(value)

    if as_names:
        return xlsf_name

    if xlsf_type == 'text':
        return safe_wrap('lorem ipsum')
    elif xlsf_type == 'integer':
        return safe_wrap(4)
    elif xlsf_type == 'decimal':
        return safe_wrap(1.2)
    elif xlsf_type == 'select one':
        return safe_wrap(u' '.join([c.get('sms_option')
                                    for c in xlsf_choices][:1]))
    elif xlsf_type == 'select all that apply':
        return safe_wrap(u' '.join([c.get('sms_option')
                                    for c in xlsf_choices][:2]))
    elif xlsf_type == 'geopoint':
        return safe_wrap('12.65 -8')
    elif xlsf_type in MEDIA_TYPES:
        exts = {'audio': 'mp3', 'video': 'avi', 'photo': 'jpg'}
        return safe_wrap('x.%s;dGhpc' % exts.get(xlsf_type, 'ext'))
    elif xlsf_type == 'barcode':
        return safe_wrap('abc')
    elif xlsf_type == 'date':
        return safe_wrap(now.strftime(xlsf_date_fmt))
    elif xlsf_type == 'datetime':
        return safe_wrap(now.strftime(xlsf_datetime_fmt))
    else:
        return safe_wrap('?')


def get_helper_text(question, json_survey):

    """ The full sentence (html) of the helper for a question

        Includes the type, a description
        and potentialy accepted values or format """

    xlsf_type = question.get('type')
    xlsf_choices = question.get('children')
    xlsf_date_fmt = json_survey.get('sms_date_format', DEFAULT_DATE_FORMAT) \
        or DEFAULT_DATE_FORMAT
    xlsf_datetime_fmt = json_survey.get('sms_date_format',
                                        DEFAULT_DATETIME_FORMAT) \
        or DEFAULT_DATETIME_FORMAT
    separator = json_survey.get('sms_separator', DEFAULT_SEPARATOR) \
        or DEFAULT_SEPARATOR

    def safe_wrap(value, xlsf_type=xlsf_type):
        value = (u'<span class="sms_autodoc_helper_type">%(type)s</span> '
                 u'<span class="sms_autodoc_helper_message">%(text)s</span>'
                 % {'type': xlsf_type, 'text': value})
        return unicode(value)

    if xlsf_type == 'text':
        return safe_wrap(u'Any string (excluding “%s”)' % separator)
    elif xlsf_type == 'integer':
        return safe_wrap('Any integer digit.')
    elif xlsf_type == 'decimal':
        return safe_wrap('A decimal or integer value.')
    elif xlsf_type == 'select one':
        helper = u'Select one of the following:'
        helper += u'<ul>'
        helper += u''.join([u'<li><span class="sms_autodoc_helper_choice_id">'
                            u'%(sms_option)s</span> <span class="sms_autodoc_'
                            u'helper_choice_label">%(label)s</span></li>'
                            % {'sms_option': c.get('sms_option'),
                               'label': c.get('label')}
                           for c in xlsf_choices])
        helper += u'</ul>'
        return safe_wrap(helper)
    elif xlsf_type == 'select all that apply':
        helper = u'Select none, one or more in:'
        helper += u'<ul>'
        helper += u''.join([u'<li><span class="sms_autodoc_helper_choice_id">'
                            u'%(sms_option)s</span> <span class="sms_autodoc_'
                            u'helper_choice_label">%(label)s</span></li>'
                            % {'sms_option': c.get('sms_option'),
                               'label': c.get('label')}
                           for c in xlsf_choices])
        helper += u'</ul>'
        return safe_wrap(helper)
    elif xlsf_type == 'geopoint':
        helper = (u'GPS coordinates as <span class="sms_autodoc_example">'
                  u'latitude longitude</span>.'
                  u'<br />Optionnaly add <span class="sms_autodoc_example">'
                  u'altitude precision</span> after. All of them are decimal.')
        return safe_wrap(helper)
    elif xlsf_type in MEDIA_TYPES:
        exts = {'audio': 'mp3', 'video': 'avi', 'photo': 'jpg'}
        helper = (u'File name and base64 data of the file as in '
                  u'<span class="sms_autodoc_example">x.%s;dGhpc</span>.'
                  u'<br />It is <strong>not</strong> intented to be filled by '
                  u'humans.' % exts.get(xlsf_type, 'ext'))
        return safe_wrap(helper)
    elif xlsf_type == 'barcode':
        return safe_wrap('A string representing the value behind the barcode.')
    elif xlsf_type == 'date':
        return safe_wrap('A date in the format: '
                         '<a href="http://strftime.org/">%s</a>'
                         % xlsf_date_fmt)
    elif xlsf_type == 'datetime':
        return safe_wrap('A datetime in the format: '
                         '<a href="http://strftime.org/">%s</a>'
                         % xlsf_datetime_fmt)
    else:
        return safe_wrap('?')


def get_autodoc_for(xform):

    """ The generated documentation in a dict (HTML output)

        line_names: example line filled with question line_names
        line_values: example line filled with fake (yet valid) data
        helpers: list of tuples (name, text) of helper texts.

        Helper texts are based on type of question and accepted values """

    json_survey = json.loads(xform.json)

    # setup formatting values
    separator = json_survey.get('sms_separator', DEFAULT_SEPARATOR) \
        or DEFAULT_SEPARATOR
    sms_allow_media = bool(json_survey.get('sms_allow_media',
                           DEFAULT_ALLOW_MEDIA) or DEFAULT_ALLOW_MEDIA)

    helpers = []
    line_names = (u'<span class="sms_autodoc_keyword">%(keyword)s</span>'
                  u'<sup>%(qid)d</sup> '
                  % {'keyword': xform.sms_id_string, 'qid': len(helpers)})
    line_values = (u'<span class="sms_autodoc_keyword">%(keyword)s</span> '
                   % {'keyword': xform.sms_id_string})
    helpers.append(('keyword', u'The keyword used to identify the form.'
                               u'<br />Omit if using a form-aware URL.'))

    for group in json_survey.get('children', {}):
        sms_field = group.get('sms_field', '')
        if not sms_field or sms_field.lower() == 'meta':
            continue

        line_values += (u'<span class="group"><span class="group_id">'
                        u'%(sep)s%(sms_field)s</span> '
                        % {'sep': separator,
                           'sms_field': group.get('sms_field')})
        line_names += (u'<span class="group"><span class="group_id">'
                       u'%(sep)s%(sms_field)s</span> '
                       % {'sep': separator,
                          'sms_field': group.get('sms_field')})

        for question in group.get('children', {}):
            type_id = question.get('type')

            if type_id in MEDIA_TYPES and not sms_allow_media:
                continue

            qid = len(helpers)
            sample = get_sample_data_for(question, json_survey)
            sample_name = get_sample_data_for(question, json_survey,
                                              as_names=True)

            line_values += (u'<span class="sms_autodoc_type_%(type)s '
                            u'sms_autodoc_type">%(value)s</span> '
                            % {'type': type_id, 'value': sample})
            line_names += (u'<span class="sms_autodoc_type_%(type)s '
                           u'sms_autodoc_type">%(value)s</span>'
                           u'<sup>%(h)s</sup> '
                           % {'type': type_id,
                              'value': sample_name, 'h': qid})
            helpers.append((sample_name,
                            get_helper_text(question, json_survey)))

        line_values += u'</span>'

    return {'line_values': line_values,
            'line_names': line_names,
            'helpers': helpers}
