from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import serializers, viewsets
from api.serializers import UserProfileSerializer, XFormSerializer,\
    ProjectSerializer, UserSerializer
from main.models import UserProfile

from odk_logger.models import XForm

from api.models import Project


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'user'


class XFormViewSet(viewsets.ModelViewSet):
    queryset = XForm.objects.all()
    serializer_class = XFormSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
