from django.db import models
from django.contrib.auth.models import User

# For now every new registration creates a new surveyor, we need a
# smart way to combine surveyors.
class Surveyor(User):
    # I need to figure out how to store an ObjectID in this model
    # not sure how long the charfield should be
    # registration_id = models.ForeignKey(
    #     ParsedInstance, related_name="surveyor registration"
    #     )

    class Meta:
        app_label = 'odk_dropbox'

    def name(self):
        return (self.first_name + " " + self.last_name).title()

