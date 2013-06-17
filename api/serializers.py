from django.contrib.auth.models import User, Group
from rest_framework import serializers

from main.models import UserProfile


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.Field(source='user.username')
    email = serializers.Field(source='user.email')
    website = serializers.Field(source='home_page')
    gravatar = serializers.Field(source='gravatar')

    class Meta:
        model = UserProfile
        fields = ('url', 'user', 'username', 'name', 'email', 'city',
                  'country',
                  'organization', 'website', 'twitter', 'gravatar',
                  'require_auth')
