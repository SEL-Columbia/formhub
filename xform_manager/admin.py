from django.contrib import admin
from .models.instance import Instance
from .models.attachment import Attachment
from .models.survey_type import SurveyType
from .models.xform import XForm

admin.site.register(Instance)
admin.site.register(Attachment)
admin.site.register(SurveyType)
admin.site.register(XForm)
