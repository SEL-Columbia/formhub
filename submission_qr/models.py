from django.db import models

from xform_manager.models import Instance
from django.contrib.auth.models import User

import datetime


class QualityReview(models.Model):
    submission = models.ForeignKey(Instance, related_name="quality_reviews")
    reviewer = models.ForeignKey(User, null=True, related_name="quality_reviews")
    score = models.IntegerField(null=True)
    comment = models.TextField(null=True)
    date_added = models.DateTimeField(default=datetime.datetime.now, editable=False)
    date_changed = models.DateTimeField(default=datetime.datetime.now, editable=False)
    hidden = models.BooleanField(default=False)
    
    class Meta:
        unique_together = (('submission', 'reviewer'))

    def __unicode__(self):
        return u"%s gave %s a score of %d" % (self.reviewer.__unicode__(), \
            self.submission.__unicode__(), \
            self.score)
