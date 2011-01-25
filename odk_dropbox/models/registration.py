from .instance import Instance

class Registration(Instance):
    # this is a way to keep track of all the instances that registered
    # surveyors.

    @classmethod
    def get_survey_owner(cls, instance):
        # get all registrations for this phone that happened before
        # this instance
        qs = cls.objects.filter(phone=instance.phone,
                                start_time__lte=instance.start_time)
        if qs.count()>0:
            most_recent_registration = qs.order_by("-start_time")[0]
            return most_recent_registration.surveyor
        return None

    class Meta:
        app_label = 'odk_dropbox'
