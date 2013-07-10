from main.models import UserProfile
from registration.backends.default.views import RegistrationView


class FHRegistrationView(RegistrationView):
    def register(self, request, **cleaned_data):
        def _get_first_last_names(name):
            name_split = name.split()
            first_name = name_split[0]
            last_name = u''
            if len(name_split) > 1:
                last_name = u' '.join(name_split[1:])
            return first_name, last_name
        new_user = \
            super(FHRegistrationView, self).register(request, **cleaned_data)
        new_profile = \
            UserProfile(user=new_user, name=cleaned_data['name'],
                        city=cleaned_data['city'],
                        country=cleaned_data['country'],
                        organization=cleaned_data['organization'],
                        home_page=cleaned_data['home_page'],
                        twitter=cleaned_data['twitter'])
        new_profile.save()
        if cleaned_data['name']:
            fn, ln = _get_first_last_names(cleaned_data['name'])
            new_user.first_name = fn
            new_user.last_name = ln
            new_user.save()
        return new_user
