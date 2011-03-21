from models import QualityReview
from django.forms import ModelForm
from xform_manager.models import Instance
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect


from django.views.decorators.csrf import csrf_exempt

#import urls

class CreateQualityReview(ModelForm):
    class Meta:
        model = QualityReview
        fields = ("score", "comment")

def ajax_post_form(instance=None, reviewer=None):
    review_form = CreateQualityReview()
#    print reverse("post_qr_url")
    ajax_post_url = "/xforms/quality_reviews/post/%d/%d" % (instance.id, 1)
    return """
    <form action='%s' method='post'><table>%s<tr><td colspan='2'><input type='submit' value='Submit' /></td></tr></table></form>
    """ % (ajax_post_url, review_form.as_table())

@csrf_exempt
def ajax_post_form_create(request, instance_id, reviewer_id):
    comment = request.POST[u'comment']
    score = request.POST[u'score']
    submission = Instance.objects.get(id=instance_id)
    reviewer = User.objects.get(id=reviewer_id)
    qr = QualityReview(comment=comment, \
            score=score, \
            submission=submission, \
            reviewer=reviewer)
    qr.save()
    return HttpResponseRedirect("/xforms/quality_reviews/")