import os
import re
import urllib2
from urlparse import urlparse

from django import forms
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from django.forms import ModelForm

from main.models import UserProfile, MetaData
from odk_viewer.models import DataDictionary
from odk_viewer.models.data_dictionary import upload_to
from registration.forms import RegistrationFormUniqueEmail
from registration.models import RegistrationProfile
from utils.country_field import COUNTRIES

FORM_LICENSES_CHOICES = (
    ('No License', 'No License'),
    ('https://creativecommons.org/licenses/by/3.0/', 'Attribution CC BY'),
    ('https://creativecommons.org/licenses/by-sa/3.0/',
     'Attribution-ShareAlike CC BY-SA'),
)

DATA_LICENSES_CHOICES = (
    ('No License', 'No License'),
    ('http://opendatacommons.org/licenses/pddl/summary/', 'PDDL'),
    ('http://opendatacommons.org/licenses/by/summary/', 'ODC-BY'),
    ('http://opendatacommons.org/licenses/odbl/summary/', 'ODBL'),
)

PERM_CHOICES = (
    ('view', 'Can view'),
    ('edit', 'Can edit'),
    ('remove', 'Remove permissions'),
)

class DataLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=DATA_LICENSES_CHOICES,
        widget=forms.Select(attrs={'disabled':'disabled', 'id':'data-license'}))


class FormLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=FORM_LICENSES_CHOICES,
        widget=forms.Select(attrs={'disabled':'disabled', 'id':'form-license'}))


class PermissionForm(forms.Form):

    for_user = forms.ChoiceField(
        widget=forms.Select())

    perm_type = forms.ChoiceField(choices=PERM_CHOICES,
        widget=forms.Select())

    def __init__(self, username):
        self.username = username
        super(PermissionForm, self).__init__()
        choices = [(u.username, u.username) for u in
            User.objects.order_by('username').exclude(username=username)]
        self.fields['for_user'].choices = choices


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user',)


class UserProfileFormRegister(forms.Form):
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

    def save(self, new_user):
        new_profile = UserProfile(user=new_user, name=self.cleaned_data['name'],
                city=self.cleaned_data['city'],
                country=self.cleaned_data['country'],
                organization=self.cleaned_data['organization'],
                home_page=self.cleaned_data['home_page'],
                twitter=self.cleaned_data['twitter'])
        new_profile.save()
        return new_profile


# order of inheritance control order of form display
class RegistrationFormUserProfile(RegistrationFormUniqueEmail, UserProfileFormRegister):
    class Meta:
        pass

    _reserved_usernames = [
        'accounts',
        'about',
        'admin',
        'clients',
        'data',
        'formhub',
        'forms',
        'maps',
        'odk',
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
    email = forms.CharField(widget=forms.TextInput(), max_length=30)

    legal_usernames_re = re.compile("^\w+$")

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if username in self._reserved_usernames:
            raise forms.ValidationError(
                u'%s is a reserved name, please choose another' % username)
        elif not self.legal_usernames_re.search(username):
            raise forms.ValidationError(
                u'username may only contain alpha-numeric characters and underscores')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(u'%s already exists' % username )

    def save(self, profile_callback=None):
        new_user = RegistrationProfile.objects.create_inactive_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'])
        UserProfileFormRegister.save(self, new_user)
        return new_user


class SourceForm(forms.Form):
    source = forms.FileField(label="Source document", required=True)


class SupportDocForm(forms.Form):
    doc = forms.FileField(label="Supporting document", required=True)


class QuickConverterFile(forms.Form):
    xls_file = forms.FileField(label="XLS File", required=False)


class QuickConverterURL(forms.Form):
    xls_url = forms.URLField(verify_exists=False, label="XLS URL", required=False)


class QuickConverter(QuickConverterFile, QuickConverterURL):
    validate = URLValidator(verify_exists=True)

    def publish(self, user):
        if self.is_valid():
            cleaned_xls_file = self.cleaned_data['xls_file']
            if not cleaned_xls_file:
                cleaned_url = self.cleaned_data['xls_url']
                cleaned_xls_file = urlparse(cleaned_url)
                cleaned_xls_file = '_'.join(cleaned_xls_file.path.split('/')[-2:])
                if cleaned_xls_file[-4:] != '.xls':
                    cleaned_xls_file += '.xls'
                cleaned_xls_file = upload_to(None, cleaned_xls_file, user.username)
                self.validate(cleaned_url)
                xls_data = ContentFile(urllib2.urlopen(cleaned_url).read())
                cleaned_xls_file = default_storage.save(cleaned_xls_file, xls_data)
            return DataDictionary.objects.create(
                user=user,
                xls=cleaned_xls_file
                )
