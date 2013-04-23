from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template.base import Template
from django.template.context import RequestContext, Context
from django.utils import simplejson
from django.utils.translation import ugettext as _

from odk_logger.models.xform import XForm
from restservice.forms import RestServiceForm
from restservice.models import RestService
from django.template.loader import render_to_string


@login_required
def add_service(request, username, id_string):
    context = RequestContext(request)
    form = RestServiceForm()
    xform = get_object_or_404(
        XForm, user__username=username, id_string=id_string)
    if request.method == 'POST':
        form = RestServiceForm(request.POST)
        context.restservice = None
        if form.is_valid():
            service_name = form.cleaned_data['service_name']
            service_url = form.cleaned_data['service_url']
            try:
                rs = RestService(service_url=service_url,
                                 name=service_name, xform=xform)
                rs.save()
            except IntegrityError:
                context.message = _(u"Service already defined.")
                context.status = 'fail'
            else:
                context.status = 'success'
                context.message = (_(u"Successfully added service %(name)s.")
                                   % {'name': service_name})
                service_tpl = render_to_string("service.html", {
                    "sv": rs, "username": xform.user.username,
                    "id_string": xform.id_string})
                context.restservice = service_tpl
        else:
            context.status = 'fail'
            context.message = _(u"Please fill in all required fields")
            if form.errors:
                for field in form:
                    context.message += Template(u"{{ field.errors }}")\
                        .render(Context({'field': field}))
        if request.is_ajax():
            response = {'status': context.status, 'message': context.message}
            if context.restservice:
                response["restservice"] = u"%s" % context.restservice
            return HttpResponse(simplejson.dumps(response))
    context.list_services = RestService.objects.filter(xform=xform)
    context.form = form
    context.username = username
    context.id_string = id_string
    return render_to_response("add-service.html", context_instance=context)


def delete_service(request, username, id_string):
    success = "FAILED"
    if request.method == 'POST':
        pk = request.POST.get('service-id')
        if pk:
            try:
                rs = RestService.objects.get(pk=int(pk))
            except RestService.DoesNotExist:
                pass
            else:
                rs.delete()
                success = "OK"
    return HttpResponse(success)
