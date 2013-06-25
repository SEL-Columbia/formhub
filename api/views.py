from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import serializers, viewsets, mixins
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

    def pre_save(self, obj):
        """
        Set any attributes on the object that are implicit in the request.
        """
        # pk and/or slug attributes are implicit in the URL.
        lookup = self.kwargs.get(self.lookup_field, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        slug_field = slug and self.slug_field or None

        if lookup:
            serializer = self.get_serializer()
            k = serializer.get_fields()[self.lookup_field]
            queryset = self.get_queryset()
            queryset = self.filter_queryset(queryset)
            if isinstance(k, serializers.HyperlinkedRelatedField):
                filter = {}
                lookup_field = '%s__%s' % (self.lookup_field, k.lookup_field)
                filter[lookup_field] = lookup
                k_obj = get_object_or_404(queryset, **filter)
                lookup = getattr(k_obj, self.lookup_field)
            setattr(obj, self.lookup_field, lookup)

        if pk:
            setattr(obj, 'pk', pk)

        if slug:
            setattr(obj, slug_field, slug)

        # Ensure we clean the attributes so that we don't eg return integer
        # pk using a string representation, as provided by the url conf kwarg.
        if hasattr(obj, 'full_clean'):
            exclude = mixins._get_validation_exclusions(
                obj, pk, slug_field, self.lookup_field)
            obj.full_clean(exclude)


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
