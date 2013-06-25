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


class ObjectLookupMixin(object):
    def get_object(self):
        """
        Incase the lookup is on an object that has been hyperlinked
        then update the queryset filter appropriately
        """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        serializer = self.get_serializer()
        lookup_field = self.lookup_field
        if self.lookup_field in serializer.get_fields():
            k = serializer.get_fields()[self.lookup_field]
            if isinstance(k, serializers.HyperlinkedRelatedField):
                lookup_field = '%s__%s' % (self.lookup_field, k.lookup_field)
        filter[lookup_field] = self.kwargs[self.lookup_field]
        return get_object_or_404(queryset,  **filter)


class UserProfileViewSet(ObjectLookupMixin, viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'user'


class XFormViewSet(viewsets.ModelViewSet):
    queryset = XForm.objects.all()
    serializer_class = XFormSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
