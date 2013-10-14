#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import re
import json
import base64
import StringIO
from datetime import datetime, date

from dict2xml import dict2xml
from django.utils.translation import ugettext as _

from odk_logger.models import XForm

from sms_support.tools import (SMS_API_ERROR, SMS_PARSING_ERROR,
                               SMS_SUBMISSION_REFUSED, sms_media_to_file,
                               generate_instance, DEFAULT_SEPARATOR,
                               NA_VALUE, META_FIELDS,
                               MEDIA_TYPES, DEFAULT_DATE_FORMAT,
                               DEFAULT_DATETIME_FORMAT,
                               SMS_SUBMISSION_ACCEPTED)


class SMSSyntaxError(ValueError):
    pass


class SMSCastingError(ValueError):

    def __init__(self, message, question=None):
        if question:
            message = _(u"%(question)s: %(message)s") % {'question': question,
                                                         'message': message}
        super(SMSCastingError, self).__init__(message)


def json2xform(jsform, form_id):
    dd = {'form_id': form_id}
    xml_head = u"<?xml version='1.0' ?>\n<%(form_id)s id='%(form_id)s'>\n" % dd
    xml_tail = u"\n</%(form_id)s>" % dd

    return xml_head + dict2xml(jsform) + xml_tail


def parse_sms_text(xform, identity, text):

    json_survey = json.loads(xform.json)

    separator = json_survey.get('sms_separator', DEFAULT_SEPARATOR) \
        or DEFAULT_SEPARATOR

    try:
        allow_media = bool(json_survey.get('sms_allow_media', False))
    except:
        raise
        allow_media = False

    xlsf_date_fmt = json_survey.get('sms_date_format', DEFAULT_DATE_FORMAT) \
        or DEFAULT_DATE_FORMAT
    xlsf_datetime_fmt = json_survey.get('sms_date_format',
                                        DEFAULT_DATETIME_FORMAT) \
        or DEFAULT_DATETIME_FORMAT

    # extract SMS data into indexed groups of values
    groups = {}
    for group in text.split(separator)[1:]:
        group_id, group_text = [s.strip() for s in group.split(None, 1)]
        groups.update({group_id: [s.strip() for s in group_text.split(None)]})

    def cast_sms_value(value, question, medias=[]):
        ''' Check data type of value and return cleaned version '''

        xlsf_type = question.get('type')
        xlsf_name = question.get('name')
        xlsf_choices = question.get('children')
        xlsf_required = bool(question.get('bind', {})
                             .get('required', '').lower() in ('yes', 'true'))

        # we don't handle constraint for now as it's a little complex and
        # unsafe.
        # xlsf_constraint=question.get('constraint')

        if xlsf_required and not len(value):
            raise SMSCastingError(_(u"Required field missing"), xlsf_name)

        def safe_wrap(func):
            try:
                return func()
            except Exception as e:
                raise SMSCastingError(_(u"%(error)s") % {'error': e},
                                      xlsf_name)

        def media_value(value, medias):
            ''' handle media values

                extract name and base64 data.
                fills the media holder with (name, data) tuple '''
            try:
                filename, b64content = value.split(';', 1)
                medias.append((filename,
                               base64.b64decode(b64content)))
                return filename
            except Exception as e:
                raise SMSCastingError(_(u"Media file format "
                                      u"incorrect. %(except)r")
                                      % {'except': e}, xlsf_name)

        if xlsf_type == 'text':
            return safe_wrap(lambda: unicode(value))
        elif xlsf_type == 'integer':
            return safe_wrap(lambda: int(value))
        elif xlsf_type == 'decimal':
            return safe_wrap(lambda: float(value))
        elif xlsf_type == 'select one':
            for choice in xlsf_choices:
                if choice.get('sms_option') == value:
                    return choice.get('name')
            raise SMSCastingError(_(u"No matching choice "
                                    u"for '%(input)s'")
                                  % {'input': value},
                                  xlsf_name)
        elif xlsf_type == 'select all that apply':
            values = [s.strip() for s in value.split()]
            ret_values = []
            for indiv_value in values:
                for choice in xlsf_choices:
                    if choice.get('sms_option') == indiv_value:
                        ret_values.append(choice.get('name'))
            return u" ".join(ret_values)
        elif xlsf_type == 'geopoint':
            err_msg = _(u"Incorrect geopoint coordinates.")
            geodata = [s.strip() for s in value.split()]
            if len(geodata) < 2 and len(geodata) > 4:
                raise SMSCastingError(err_msg, xlsf_name)
            try:
                # check that latitude and longitude are floats
                lat, lon = [float(v) for v in geodata[:2]]
                # and within sphere boundaries
                if lat < -90 or lat > 90 or lon < -180 and lon > 180:
                    raise SMSCastingError(err_msg, xlsf_name)
                if len(geodata) == 4:
                    # check that altitude and accuracy are integers
                    [int(v) for v in geodata[2:4]]
                elif len(geodata) == 3:
                    # check that altitude is integer
                    int(geodata[2])
            except Exception as e:
                raise SMSCastingError(e.message, xlsf_name)
            return " ".join(geodata)

        elif xlsf_type in MEDIA_TYPES:
            # media content (image, video, audio) must be formatted as:
            # file_name;base64 encodeed content.
            # Example: hello.jpg;dGhpcyBpcyBteSBwaWN0dXJlIQ==
            return media_value(value, medias)
        elif xlsf_type == 'barcode':
            return safe_wrap(lambda: unicode(value))
        elif xlsf_type == 'date':
            return safe_wrap(lambda: datetime.strptime(value,
                                                       xlsf_date_fmt).date())
        elif xlsf_type == 'datetime':
            return safe_wrap(lambda: datetime.strptime(value,
                                                       xlsf_datetime_fmt))
        raise SMSCastingError(_(u"Unsuported column '%(type)s'")
                              % {'type': xlsf_type}, xlsf_name)

    def get_meta_value(xlsf_type, identity):
        ''' XLSForm Meta field value '''
        if xlsf_type in ('deviceid', 'subscriberid', 'imei'):
            return NA_VALUE
        elif xlsf_type in ('start', 'end'):
            return datetime.now().isoformat()
        elif xlsf_type == 'today':
            return date.today().isoformat()
        elif xlsf_type == 'phonenumber':
            return identity
        return NA_VALUE

    # holder for all properly formated answers
    survey_answers = {}
    # list of (name, data) tuples for media contents
    medias = []
    # keep track of required questions

    # loop on all XLSForm questions
    for expected_group in json_survey.get('children', [{}]):
        if not expected_group.get('type') == 'group':
            # non-grouped questions are not valid for SMS
            continue

        # retrieve part of SMS text for this group
        group_id = expected_group.get('sms_field')
        answers = groups.get(group_id)
        if not group_id or (not answers and not group_id.startswith('meta')):
            # group is not meant to be filled by SMS
            # or hasn't been filled
            continue

        # Add a holder for this group's answers data
        survey_answers.update({expected_group.get('name'): {}})

        # retrieve question definition for each answer
        egroups = expected_group.get('children', [{}])

        # number of intermediate, omited questions (medias)
        step_back = 0
        for idx, question in enumerate(egroups):

            real_value = None

            question_type = question.get('type')
            if question_type in ('calculate', 'note'):
                # 'calculate' question are not implemented.
                # 'note' ones are just meant to be displayed on device
                continue

            if not allow_media and question_type in MEDIA_TYPES:
                # if medias for SMS has not been explicitly allowed
                # they are considered excluded.
                step_back += 1
                continue

            # pop the number of skipped questions
            # so that out index is valid even if the form
            # contain medias questions (and medias are disabled)
            sidx = idx - step_back

            if question_type in META_FIELDS:
                # some question are not to be fed by users
                real_value = get_meta_value(xlsf_type=question_type,
                                            identity=identity)
            else:
                # actual SMS-sent answer.
                # Only last answer/question of each group is allowed
                # to have multiple spaces
                if idx == len(egroups) - 1:
                    answer = u" ".join(answers[sidx:])
                else:
                    answer = answers[sidx]

            if real_value is None:
                # retrieve actual value and fail if it doesn't meet reqs.
                real_value = cast_sms_value(answer,
                                            question=question, medias=medias)

            # set value to its question name
            survey_answers[expected_group.get('name')] \
                .update({question.get('name'): real_value})

    return survey_answers, medias


def process_incoming_smses(username, incomings,
                           id_string=None):
    ''' Process Incoming (identity, text[, id_string]) SMS '''

    xforms = []
    medias = []
    responses = []
    json_submissions = []
    resp_str = {'success': _(u"[SUCCESS] Your submission has been accepted. "
                             u"It's ID is {{ id }}.")}

    def process_incoming(incoming, id_string):
        # assign variables
        if len(incoming) >= 2:
            identity = incoming[0].strip().lower()
            text = incoming[1].strip().lower()
            # if the tuple contain an id_string, use it, otherwise default
            if len(incoming) and id_string is None >= 3:
                id_string = incoming[2]
        else:
            responses.append({'code': SMS_API_ERROR,
                              'text': _(u"Missing 'identity' "
                                        u"or 'text' field.")})
            return

        if not len(identity.strip()) or not len(text.strip()):
            responses.append({'code': SMS_API_ERROR,
                              'text': _(u"'identity' and 'text' fields can "
                                        u"not be empty.")})
            return

        # if no id_string has been supplied
        # we expect the SMS to be prefixed with the form's sms_id_string
        if id_string is None:
            keyword, text = [s.strip() for s in text.split(None, 1)]
            xform = XForm.objects.get(user__username=username,
                                      sms_id_string=keyword)
        else:
            xform = XForm.objects.get(user__username=username,
                                      id_string=id_string)

        if not xform.allows_sms:
            responses.append({'code': SMS_SUBMISSION_REFUSED,
                              'text': _(u"The form '%(id_string)s' does not "
                                        u"accept SMS submissions.")
                             % {'id_string': xform.id_string}})
            return

        # parse text into a dict object of groups with values
        json_submission, medias_submission = parse_sms_text(xform,
                                                            identity, text)

        # retrieve sms_response if exist in the form.
        json_survey = json.loads(xform.json)
        if json_survey.get('sms_response'):
            resp_str.update({'success': json_survey.get('sms_response')})

        # check that the form contains at least one filled group
        meta_groups = sum([1 for k in json_submission.keys()
                           if k.startswith('meta')])
        if len(json_submission.keys()) <= meta_groups:
            responses.append({'code': SMS_PARSING_ERROR,
                              'text': _(u"There must be at least one group of "
                                        u"questions filled.")})
            return

        # check that required fields have been filled
        required_fields = [f.get('name')
                           for g in json_survey.get('children', {})
                           for f in g.get('children', {})
                           if f.get('bind', {}).get('required', 'no') == 'yes']
        submitted_fields = {}
        for group in json_submission.values():
            submitted_fields.update(group)

        for field in required_fields:
            if not submitted_fields.get(field):
                responses.append({'code': SMS_SUBMISSION_REFUSED,
                                  'text': _(u"Required field `%(field)s` is  "
                                            u"missing.") % {'field': field}})
                return

        # convert dict object into an XForm string
        xml_submission = json2xform(jsform=json_submission,
                                    form_id=xform.id_string)

        # process_incoming expectes submission to be a file-like object
        xforms.append(StringIO.StringIO(xml_submission))
        medias.append(medias_submission)
        json_submissions.append(json_submission)

    for incoming in incomings:
        try:
            process_incoming(incoming, id_string)
        except Exception as e:
            responses.append({'code': SMS_PARSING_ERROR, 'text': str(e)})

    for idx, xform in enumerate(xforms):
        # generate_instance expects media as a request.FILES.values() list
        xform_medias = [sms_media_to_file(f, n) for n, f in medias[idx]]
        # create the instance in the data base
        response = generate_instance(username=username,
                                     xml_file=xform,
                                     media_files=xform_medias)
        if response.get('code') == SMS_SUBMISSION_ACCEPTED:
            success_response = re.sub(r'{{\s*[i,d,I,D]{2}\s*}}',
                                      response.get('id'),
                                      resp_str.get('success'), re.I)

            # extend success_response with data from the answers
            data = {}
            for g in json_submissions[idx].values():
                data.update(g)
            success_response = success_response.replace('${',
                                                        '{').format(**data)
            response.update({'text': success_response})
        responses.append(response)

    return responses
