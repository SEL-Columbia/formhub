from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.http import HttpResponseForbidden, HttpResponse, \
                        HttpResponseBadRequest, Http404

from utils.logger_tools import disposition_ext_and_date
from odk_logger.models import XForm
from utils.user_auth import has_permission, helper_auth_helper
from logbook.export_tools import generate_pdf, generate_frp_xls


def awc_pdf_export(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    permit_nums = request.GET.getlist('permit')
    submission_type = request.GET.get('submissionType', '')
    observations = request.GET.get('observations', None)
    if observations:
        observations = ["uuid:" + x for x in observations.strip().split(",")]

    if not observations or len(observations) < 1 or len(observations) > 5:
        return HttpResponseBadRequest("Provide between 1 and 5 observations")

    if len(permit_nums) == 0:
        return HttpResponseBadRequest("Must provide at least one permit")

    pdf = generate_pdf(id_string, submission_type, observations,
        user=owner, permit_nums=permit_nums)                            #TODO - Get full name. Also, observer or user?
    response = HttpResponse(pdf, mimetype="application/pdf")
    response['Content-Disposition'] = disposition_ext_and_date(
        '-'.join(permit_nums), 'pdf')
    response['Content-Length'] = len(pdf)
    return response

def frp_xls_export(request, username, id_string):
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))

    permit_nums = request.GET.getlist('permit')
    biol_date = request.GET.get('biologistContactDate', '')
    if len(permit_nums) != 1:
        return HttpResponseBadRequest("Must provide a single permit")

    pdf = generate_frp_xls(id_string, biol_date,
        user=owner, permit_nums=permit_nums)
    response = HttpResponse(pdf, mimetype="application/vnd.ms-excel")
    response['Content-Disposition'] = disposition_ext_and_date(
        '-'.join(permit_nums), 'xls')
    return response
