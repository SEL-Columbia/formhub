from django.contrib import admin
import reversion
from odk_logger.models import XForm, Instance


class FormAdmin(admin.ModelAdmin):

    exclude = ('user',)
    list_display = ('id_string', 'downloadable', 'shared')

    # A user should only see forms that belong to him.
    def queryset(self, request):
        qs = super(FormAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

admin.site.register(XForm, FormAdmin)


class InstanceAdmin(reversion.admin.VersionAdmin):
    pass

admin.site.register(Instance, InstanceAdmin)
