from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.utils import IntegrityError
from django.shortcuts import render_to_response
from django.template.base import Template
from django.template.context import RequestContext, Context
from django.utils import simplejson
from odk_logger.models.xform import XForm
from restservice.forms import RestServiceForm
from restservice.models import RestService


@login_required
def add_service(request, username, id_string):
    context = RequestContext(request)
    form = RestServiceForm()
    if request.method == 'POST':
        form = RestServiceForm(request.POST)
        if form.is_valid():
            service_name = form.cleaned_data['service_name']
            service_url = form.cleaned_data['service_url']
            xform = XForm.objects.get(user__username=username,\
                id_string=id_string)
            try:
                rs = RestService(service_url=service_url,
                                    name=service_name, xform=xform)
                rs.save()
            except IntegrityError:
                context.message = u"Service already defined."
                context.status = 'fail'
            else:
                context.status = 'success'
                context.message \
                        = u"Successfully added service %s." % service_name
        else:
            context.status = 'fail'
            context.message = u"Please fill in all required fields"
            if form.errors:
                for field in form:
                    context.message += Template(u"{{ field.errors }}")\
                                        .render(Context({'field': field}))
        if request.is_ajax():
            response = {'status': context.status, 'message': context.message}
            return HttpResponse(simplejson.dumps(response))
    context.form = form
    context.username = username
    context.id_string = id_string
    return render_to_response("add-service.html", context_instance=context)