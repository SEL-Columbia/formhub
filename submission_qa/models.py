from django.db import models

from parsed_xforms.models import ParsedInstance
from django.contrib.auth.models import User

import datetime


class QualityReview(models.Model):
    submission = models.ForeignKey(ParsedInstance, related_name="quality_reviews")
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

# class ReviewerDistrictSummary(models.Model):
#     reviewer = models.ForeignKey(User, null=True)
# #     district = models.ForeignKey(District, null=True)
#     total_reviews = models.IntegerField()
#     average_score = models.FloatField()
# 
#     def recalculate(self):
#         qrs = QualityReview.objects.filter(reviewer=self.reviewer, \
#                             hidden=False)
#         qr_count = qrs.count()
#         qr_score_array = [q.score for q in qrs]
#         sum = 0
#         for score in qr_score_array:
#             sum += score
#         qr_sum
#         self.total_reviews = qr_count
#         self.average_score = qr_sum / qr_count
#      
#      def __unicode__(self):
#          return u"%s reviewed %d submissions in %s with an average score of %d" % \
#                  (self.reviewer.__unicode__(), \
#                  self.total_reviews,
#                  self.district.__unicode__(), \
#                  self.average_score)
#     class Meta:
#         unique_together = (('reviewer', 'district'))
# 

#from django.db.models.signals import post_save
#post_save.connect(_tally_reviews, sender=QualityReview)

#def _tally_reviews(sender, **kwargs)