import copy

from django.forms import widgets
from django.contrib.auth.models import User

from rest_framework import serializers

from main.models import UserProfile
from main.forms import UserProfileForm, RegistrationFormUserProfile

from odk_logger.models import XForm

from api.models import Project, OrganizationProfile, Team
from api.fields import HyperlinkedMultiIdentityField,\
    HyperlinkedMultiRelatedField

from api import tools as utils


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')
        #exclude = ('groups', 'user_permissions')
        lookup_field = 'username'


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.WritableField(source='user.username')
    email = serializers.WritableField(source='user.email')
    website = serializers.WritableField(source='home_page', required=False)
    gravatar = serializers.Field(source='gravatar')
    password = serializers.WritableField(
        source='user.password', widget=widgets.PasswordInput(), required=False)
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('url', 'username', 'name', 'password', 'email', 'city',
                  'country', 'organization', 'website', 'twitter', 'gravatar',
                  'require_auth', 'user')
        lookup_field = 'user'

    def to_native(self, obj):
        """
        Serialize objects -> primitives.
        """
        ret = super(UserProfileSerializer, self).to_native(obj)
        if 'password' in ret:
            del ret['password']
        return ret

    def restore_object(self, attrs, instance=None):
        def _get_first_last_names(name):
            name_split = name.split()
            first_name = name_split[0]
            last_name = u''
            if len(name_split) > 1:
                last_name = u' '.join(name_split[1:])
            return first_name, last_name
        params = copy.deepcopy(attrs)
        username = attrs.get('user.username', None)
        password = attrs.get('user.password', None)
        name = attrs.get('name', None)
        email = attrs.get('user.email', None)
        if username:
            params['username'] = username
        if email:
            params['email'] = email
        if password:
            params.update({'password1': password, 'password2': password})
        if instance:
            form = UserProfileForm(params, instance=instance)
            # form.is_valid affects instance object for partial updates [PATCH]
            # so only use it for full updates [PUT], i.e shallow copy effect
            if not self.partial and form.is_valid():
                instance = form.save()
            # get user
            if email:
                instance.user.email = form.cleaned_data['email']
            if name:
                first_name, last_name = _get_first_last_names(name)
                instance.user.first_name = first_name
                instance.user.last_name = last_name
            if email or name:
                instance.user.save()
            return super(
                UserProfileSerializer, self).restore_object(attrs, instance)
            #return instance  # TODO: updates
        form = RegistrationFormUserProfile(params)
        # does not require captcha
        form.REGISTRATION_REQUIRE_CAPTCHA = False
        if form.is_valid():
            first_name, last_name = _get_first_last_names(name)
            new_user = User(username=username, first_name=first_name,
                            last_name=last_name, email=email)
            new_user.set_password(password)
            new_user.save()
            created_by = self.context['request'].user
            profile = UserProfile(
                user=new_user, name=attrs.get('name', u''),
                created_by=created_by,
                city=attrs.get('city', u''),
                country=attrs.get('country', u''),
                organization=attrs.get('organization', u''),
                home_page=attrs.get('home_page', u''),
                twitter=attrs.get('twitter', u''))
            return profile
        else:
            self.errors.update(form.errors)
        return attrs


class XFormSerializer(serializers.HyperlinkedModelSerializer):
    url = HyperlinkedMultiIdentityField(
        view_name='xform-detail',
        lookup_fields=(('pk', 'pk'), ('owner', 'user')))
    formid = serializers.Field(source='id')
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        source='user', lookup_field='username')
    public = serializers.BooleanField(
        source='shared', widget=widgets.CheckboxInput())
    public_data = serializers.BooleanField(
        source='shared_data')

    class Meta:
        model = XForm
        read_only_fields = (
            'json', 'xml', 'date_created', 'date_modified', 'encrypted')
        exclude = ('id', 'json', 'xml', 'xls', 'user',
                   'has_start_time', 'shared', 'shared_data')


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    url = HyperlinkedMultiIdentityField(
        view_name='project-detail',
        lookup_fields=(('pk', 'pk'), ('owner', 'organization')))
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        source='organization', lookup_field='username')
    created_by = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)

    class Meta:
        model = Project
        exclude = ('organization', 'created_by')

    def restore_object(self, attrs, instance=None):
        if instance:
            return super(ProjectSerializer, self)\
                .restore_object(attrs, instance)
        if 'request' in self.context:
            created_by = self.context['request'].user
            return Project(
                name=attrs.get('name'),
                organization=attrs.get('organization'),
                created_by=created_by,)
        return attrs


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    org = serializers.WritableField(source='user.username')
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)
    creator = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)

    class Meta:
        model = OrganizationProfile
        lookup_field = 'user'
        exclude = ('created_by', 'is_organization', 'organization')

    def restore_object(self, attrs, instance=None):
        if instance:
            return super(OrganizationSerializer, self)\
                .restore_object(attrs, instance)
        org = attrs.get('user.username', None)
        org_exists = False
        try:
            User.objects.get(username=org)
        except User.DoesNotExist:
            pass
        else:
            self.errors['org'] = u'Organization %s already exists.' % org
            org_exists = True
        creator = None
        if 'request' in self.context:
            creator = self.context['request'].user
        if org and creator and not org_exists:
            attrs['organization'] = attrs.get('name')
            orgprofile = utils.create_organization_object(org, creator, attrs)
            return orgprofile
        if not org:
            self.errors['org'] = u'org is required!'
        return attrs


class TeamSerializer(serializers.Serializer):
    url = HyperlinkedMultiIdentityField(
        view_name='team-detail',
        lookup_fields=(('pk', 'pk'), ('owner', 'organization')))
    name = serializers.CharField(max_length=100, source='team_name')
    organization = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username',
        source='organization',
        queryset=User.objects.filter(
            pk__in=OrganizationProfile.objects.values('user')))
    projects = HyperlinkedMultiRelatedField(
        view_name='project-detail', source='projects', many=True,
        queryset=Project.objects.all(), read_only=True,
        lookup_fields=(('pk', 'pk'), ('owner', 'organization')))

    def restore_object(self, attrs, instance=None):
        org = attrs.get('organization', None)
        projects = attrs.get('projects', [])
        if instance:
            instance.organization = org if org else instance.organization
            instance.name = attrs.get('team_name', instance.name)
            instance.projects.clear()
            for project in projects:
                instance.projects.add(project)
            return instance
        team_name = attrs.get('team_name', None)
        if not team_name:
            self.errors['name'] = u'A team name is required'
            return attrs
        return Team(organization=org, name=team_name)
