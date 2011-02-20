from models import QualityReview
from parsed_xforms.models import ParsedInstance

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.generic.create_update import create_object, update_object
from django.forms import ModelForm
from django.core.urlresolvers import reverse

def list(request, group_name=None):
    qrs = QualityReview.objects.all()
    pis = ParsedInstance.objects.all()
#    if group_name:
#        qrs = qrs.filter(group_name=group_name)
    info = {'qrs':qrs}
    info['qr_count'] = ParsedInstance.objects.count()
    info['pis'] = pis
    info['show_hide_review_url'] = "/xforms/quality_reviews/"
    info['new_review_url'] = "/xforms/quality_reviews/new/" #def a cleaner way to do this
    return render_to_response("list.html", info)

class CreateQualityReview(ModelForm):
    class Meta:
        model = QualityReview
        exclude = ('hidden')
#        exclude = ('submission', 'hidden')
    #    fields = ("",)

def new_review(request, pi_id, group_name=None):
    submission = ParsedInstance.objects.get(id=pi_id)
#    reviewer = "whoever is logged in "
    return create_object(
        request=request,
        form_class=CreateQualityReview,
        template_name="form.html",
        post_save_redirect=reverse("list_quality_reviews"),
        )

def show_hide(request, show_hide, qr_id):
    qr = QualityReview.objects.get(id=qr_id)
    if show_hide=="show":
        qr.hidden=False
        qr.save()
    elif show_hide=="hide":
        qr.hidden=True
        qr.save()
    return HttpResponseRedirect(reverse("list_quality_reviews"))
