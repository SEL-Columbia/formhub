import re
import urllib2
from urlparse import urlparse

from django import forms
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from django.forms import ModelForm
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf import settings
from recaptcha.client import captcha

from main.models import UserProfile
from odk_viewer.models.data_dictionary import upload_to
from registration.forms import RegistrationFormUniqueEmail
from registration.models import RegistrationProfile
from utils.country_field import COUNTRIES
from utils.logger_tools import publish_xls_form

FORM_LICENSES_CHOICES = (
    ('No License', ugettext_lazy('No License')),
    ('https://creativecommons.org/licenses/by/3.0/',
     ugettext_lazy('Attribution CC BY')),
    ('https://creativecommons.org/licenses/by-sa/3.0/',
     ugettext_lazy('Attribution-ShareAlike CC BY-SA')),
)

DATA_LICENSES_CHOICES = (
    ('No License', ugettext_lazy('No License')),
    ('http://opendatacommons.org/licenses/pddl/summary/',
     ugettext_lazy('PDDL')),
    ('http://opendatacommons.org/licenses/by/summary/',
     ugettext_lazy('ODC-BY')),
    ('http://opendatacommons.org/licenses/odbl/summary/',
     ugettext_lazy('ODBL')),
)

PERM_CHOICES = (
    ('view', ugettext_lazy('Can view')),
    ('edit', ugettext_lazy('Can edit')),
    ('remove', ugettext_lazy('Remove permissions')),
)


class DataLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=DATA_LICENSES_CHOICES,
                              widget=forms.Select(
                                  attrs={'disabled': 'disabled',
                                         'id': 'data-license'}))


class FormLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=FORM_LICENSES_CHOICES,
                              widget=forms.Select(
                                  attrs={'disabled': 'disabled',
                                         'id': 'form-license'}))


class PermissionForm(forms.Form):
    for_user = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'autocomplete',
                'data-provide': 'typeahead',
                'autocomplete': 'off'
            })
    )
    perm_type = forms.ChoiceField(choices=PERM_CHOICES, widget=forms.Select())

    def __init__(self, username):
        self.username = username
        super(PermissionForm, self).__init__()


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user',)
    email = forms.EmailField(widget=forms.TextInput())


class UserProfileFormRegister(forms.Form):

    REGISTRATION_REQUIRE_CAPTCHA = settings.REGISTRATION_REQUIRE_CAPTCHA
    RECAPTCHA_PUBLIC_KEY = settings.RECAPTCHA_PUBLIC_KEY
    RECAPTCHA_HTML = captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY,
                                         use_ssl=settings.RECAPTCHA_USE_SSL)

    name = forms.CharField(widget=forms.TextInput(), required=False,
                           max_length=255)
    city = forms.CharField(widget=forms.TextInput(), required=False,
                           max_length=255)
    country = forms.ChoiceField(widget=forms.Select(), required=False,
                                choices=COUNTRIES, initial='ZZ')
    organization = forms.CharField(widget=forms.TextInput(), required=False,
                                   max_length=255)
    home_page = forms.CharField(widget=forms.TextInput(), required=False,
                                max_length=255)
    twitter = forms.CharField(widget=forms.TextInput(), required=False,
                              max_length=255)

    recaptcha_challenge_field = forms.CharField(required=False, max_length=512)
    recaptcha_response_field = forms.CharField(
        max_length=100, required=settings.REGISTRATION_REQUIRE_CAPTCHA)

    def save(self, new_user):
        new_profile = \
            UserProfile(user=new_user, name=self.cleaned_data['name'],
                        city=self.cleaned_data['city'],
                        country=self.cleaned_data['country'],
                        organization=self.cleaned_data['organization'],
                        home_page=self.cleaned_data['home_page'],
                        twitter=self.cleaned_data['twitter'])
        new_profile.save()
        return new_profile


# order of inheritance control order of form display
class RegistrationFormUserProfile(RegistrationFormUniqueEmail,
                                  UserProfileFormRegister):
    class Meta:
        pass

    _reserved_usernames = [
        'accounts',
        'about',
        'admin',
        'clients',
        'crowdform',
        'crowdforms',
        'data',
        'formhub',
        'forms',
        'maps',
        'odk',
        'people',
        'submit',
        'submission',
        'support',
        'syntax',
        'xls2xform',
        'users',
        'worldbank',
        'unicef',
        'who',
        'wb',
        'wfp',
        'save',
        'ei',
        'modilabs',
        'mvp',
        'unido',
        'unesco',
        'savethechildren',
        'worldvision',
        'afsis'
    ]

    username = forms.CharField(widget=forms.TextInput(), max_length=30)
    email = forms.EmailField(widget=forms.TextInput())

    legal_usernames_re = re.compile("^\w+$")

    def clean(self):
        cleaned_data = super(UserProfileFormRegister, self).clean()

        # don't check captcha if it's disabled
        if not self.REGISTRATION_REQUIRE_CAPTCHA:
            if 'recaptcha_response_field' in self._errors:
                del self._errors['recaptcha_response_field']
            return cleaned_data

        response = captcha.submit(
            cleaned_data.get('recaptcha_challenge_field'),
            cleaned_data.get('recaptcha_response_field'),
            settings.RECAPTCHA_PRIVATE_KEY,
            None)

        if not response.is_valid:
            raise forms.ValidationError(_(u"The Captcha is invalid. "
                                          u"Please, try again."))
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if username in self._reserved_usernames:
            raise forms.ValidationError(
                _(u'%s is a reserved name, please choose another') % username)
        elif not self.legal_usernames_re.search(username):
            raise forms.ValidationError(
                _(u'username may only contain alpha-numeric characters and '
                  u'underscores'))
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_(u'%s already exists') % username)

    def save(self, profile_callback=None):
        new_user = RegistrationProfile.objects.create_inactive_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'])
        UserProfileFormRegister.save(self, new_user)
        return new_user


class SourceForm(forms.Form):
    source = forms.FileField(label=ugettext_lazy(u"Source document"),
                             required=True)


class SupportDocForm(forms.Form):
    doc = forms.FileField(label=ugettext_lazy(u"Supporting document"),
                          required=True)


class MediaForm(forms.Form):
    media = forms.FileField(label=ugettext_lazy(u"Media upload"),
                            required=True)

    def clean_media(self):
        data_type = self.cleaned_data['media'].content_type
        if not data_type in ['image/jpeg', 'image/png', 'audio/mpeg']:
            raise forms.ValidationError('Only these media types are \
                                        allowed .png .jpg .mp3 .3gp .wav')


class MapboxLayerForm(forms.Form):
    map_name = forms.CharField(widget=forms.TextInput(), required=True,
                               max_length=255)
    attribution = forms.CharField(widget=forms.TextInput(), required=False,
                                  max_length=255)
    link = forms.URLField(label=ugettext_lazy(u'JSONP url'),
                          required=True)


class QuickConverterFile(forms.Form):
    xls_file = forms.FileField(
        label=ugettext_lazy(u'XLS File'), required=False)


class QuickConverterURL(forms.Form):
    xls_url = forms.URLField(label=ugettext_lazy('XLS URL'),
                             required=False)


class QuickConverterDropboxURL(forms.Form):
    dropbox_xls_url = forms.URLField(
        label=ugettext_lazy('XLS URL'), required=False)


class QuickConverter(QuickConverterFile, QuickConverterURL,
                     QuickConverterDropboxURL):
    validate = URLValidator()

    def publish(self, user, id_string=None):
        if self.is_valid():
            cleaned_xls_file = self.cleaned_data['xls_file']
            if not cleaned_xls_file:
                cleaned_url = self.cleaned_data['xls_url']
                if cleaned_url.strip() == u'':
                    cleaned_url = self.cleaned_data['dropbox_xls_url']
                cleaned_xls_file = urlparse(cleaned_url)
                cleaned_xls_file = \
                    '_'.join(cleaned_xls_file.path.split('/')[-2:])
                if cleaned_xls_file[-4:] != '.xls':
                    cleaned_xls_file += '.xls'
                cleaned_xls_file = \
                    upload_to(None, cleaned_xls_file, user.username)
                self.validate(cleaned_url)
                xls_data = ContentFile(urllib2.urlopen(cleaned_url).read())
                cleaned_xls_file = \
                    default_storage.save(cleaned_xls_file, xls_data)
            # publish the xls
            return publish_xls_form(cleaned_xls_file, user, id_string)


class ActivateSMSSupportFom(forms.Form):

    enable_sms_support = forms.TypedChoiceField(coerce=lambda x: x == 'True',
                                                choices=((False, 'No'),
                                                         (True, 'Yes')),
                                                widget=forms.Select,
                                                label=ugettext_lazy(
                                                    u"Enable SMS Support"))
    sms_id_string = forms.CharField(max_length=50, required=True,
                                    label=ugettext_lazy(u"SMS Keyword"))

    def clean_sms_id_string(self):
        sms_id_string = self.cleaned_data.get('sms_id_string', '').strip()

        if not re.match(r'^[a-z0-9\_\-]+$', sms_id_string):
            raise forms.ValidationError(u"id_string can only contain alphanum"
                                        u" characters")

        return sms_id_string
