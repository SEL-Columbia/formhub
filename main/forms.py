from django import forms
from django.contrib.auth.models import User
from registration.forms import RegistrationFormUniqueEmail
from main.models import UserProfile, MetaData
from registration.models import RegistrationProfile
from utils.country_field import COUNTRIES
from django.forms import ModelForm
import re

FORM_LICENSES_CHOICES = (
    ('Attribution CC BY', 'Attribution CC BY'),
    ('Attribution-ShareAlike CC BY-SA', 'Attribution-ShareAlike CC BY-SA')
)

class FormLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=FORM_LICENSES_CHOICES)

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user',)

class UserProfileFormRegister(forms.Form):
    name = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    city = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    country = forms.ChoiceField(widget=forms.Select(), required=False, choices=COUNTRIES, initial='ZZ')
    organization = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    home_page = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    twitter = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)

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

    illegal_usernames_re = re.compile(" |#|%|\&|\*|{|}|\|:|\"|'|\?|>|<|/|\\\\")

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if username in self._reserved_usernames:
            raise forms.ValidationError(u'%s is a reserved name, please choose another' % username)
        elif self.illegal_usernames_re.search(username):
            raise forms.ValidationError(u'username cannot contain #%&*{}\:"\'?></\\ or any spaces')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(u'%s already exists' % username )

    def save(self, profile_callback=None):
        new_user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['username'],
                password=self.cleaned_data['password1'],
                email=self.cleaned_data['email'])
        UserProfileFormRegister.save(self, new_user)
        return new_user

