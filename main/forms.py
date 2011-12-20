from django import forms
from registration.forms import RegistrationForm
from main.models import UserProfile
from registration.models import RegistrationProfile
from country_field import COUNTRIES

class RegistrationFormUserProfile(RegistrationForm):
    username = forms.CharField(widget=forms.TextInput(), max_length=30)
    email = forms.CharField(widget=forms.TextInput(), max_length=30)
    name = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    city = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    country = forms.ChoiceField(widget=forms.Select(), required=False, choices=COUNTRIES, initial='ZZ')
    organization = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    home_page = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)
    twitter = forms.CharField(widget=forms.TextInput(), required=False, max_length=255)

    def save(self, profile_callback=None):
        new_user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['username'].lower(),
                password=self.cleaned_data['password1'],
                email=self.cleaned_data['email'])

        new_profile = UserProfile(user=new_user, name=self.cleaned_data['name'],
                city=self.cleaned_data['city'],
                country=self.cleaned_data['country'],
                organization=self.cleaned_data['organization'],
                home_page=self.cleaned_data['home_page'],
                twitter=self.cleaned_data['twitter'])
        new_profile.save()

        return new_user

