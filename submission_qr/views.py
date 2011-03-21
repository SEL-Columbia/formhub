from models import QualityReview
from xform_manager.models import Instance

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.generic.create_update import create_object, update_object
from django.forms import ModelForm
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from . import forms

def list(request, group_name=None):
    qrs = QualityReview.objects.all()
    pis = Instance.objects.all()
#    if group_name:
#        qrs = qrs.filter(group_name=group_name)
    info = {'qrs':qrs}
    info['qr_count'] = Instance.objects.count()
    info['pis'] = pis
    info['show_hide_review_url'] = "/xforms/quality_reviews/"
    info['new_review_url'] = "/xforms/quality_reviews/new/" #def a cleaner way to do this
    return render_to_response("list.html", info)

def new_review(request, pi_id, group_name=None):
    submission = Instance.objects.get(id=pi_id)
#    reviewer = "whoever is logged in "
    return create_object(
        request=request,
        form_class=forms.CreateQualityReview,
        template_name="form.html",
        post_save_redirect=reverse("list_quality_reviews"),
        )

def list_reviews_for_submission(request, submission_id):
    info = {'submission': Instance.objects.get(id=submission_id)}
    return render_to_response("list_reviews.html", info)

def show_hide(request, show_hide, qr_id):
    qr = QualityReview.objects.get(id=qr_id)
    if show_hide=="show":
        qr.hidden=False
        qr.save()
    elif show_hide=="hide":
        qr.hidden=True
        qr.save()
    return HttpResponseRedirect(reverse("list_quality_reviews"))

from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
def ajax_review_post(request, submission_id, reviewer_id):
    submission = Instance.objects.get(id=submission_id)
    reviewer = User.objects.get(id=reviewer_id)
    try:
        qr = QualityReview.objects.get(submission=submission, \
            reviewer=reviewer)
        qr.score = request.POST[u'score']
        qr.comment = request.POST[u'comment']
    except:
        qr = QualityReview(submission=submission, \
                reviewer=reviewer, score=request.POST[u'score'], \
                comment=request.POST[u'comment'])
    try:
        qr.save()
        errors = False
    except ValueError, e:
        errors = "Error: %s" % e.message
    
    return score_partial(submission, reviewer, errors=errors)

from django.template.loader import render_to_string

def score_partial_request(request, submission_id, reviewer_id):
    user = User.objects.get(id=reviewer_id)
    pi = Instance.objects.get(id=submission_id)
    return score_partial(pi, user)

def score_partial(submission, reviewer, as_string=False, errors=""):
    info = {'user': reviewer,\
            'submission': submission}
    try:
        existing_qr = QualityReview.objects.get(reviewer=reviewer, submission=submission)
    except:
        existing_qr = None
    info['reviewer'] = reviewer
    if errors is not "":
        info['errors'] = errors
    else:
        info['errors'] = False
    info['reviews'] = info['submission'].quality_reviews.exclude(reviewer=reviewer)
    info['review_form'] = forms.CreateQualityReview(instance=existing_qr)
    info['qr_exists'] = existing_qr is not None
    info['review'] = existing_qr
    info['submission_qr_url'] = "/xforms/quality_reviews"
    if as_string:
        return render_to_string("score_partial.html", info)
    else:
        return render_to_response("score_partial.html", info)