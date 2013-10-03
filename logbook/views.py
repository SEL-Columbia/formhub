from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.http import HttpResponseForbidden, HttpResponse

#TODO may need this eventually??
# from xls_writer import XlsWriter
from utils.logger_tools import disposition_ext_and_date
from odk_logger.models import XForm
from utils.user_auth import has_permission, helper_auth_helper
from logbook.export_tools import generate_pdf


def pdf_export(request, username, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message = "HELLO!!"
    owner = get_object_or_404(User, username=username)
    xform = get_object_or_404(XForm, id_string=id_string, user=owner)
    helper_auth_helper(request)
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(_(u'Not shared.'))
    pdf = generate_pdf(id_string, user=owner)
    response = HttpResponse(pdf, mimetype="application/pdf")
    response['Content-Disposition'] = \
        disposition_ext_and_date(id_string, 'pdf')
    return response

