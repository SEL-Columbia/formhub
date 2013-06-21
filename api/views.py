from rest_framework import viewsets
from api.serializers import UserProfileSerializer, XFormSerializer
from main.models import UserProfile

from odk_logger.models import XForm


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class XFormViewSet(viewsets.ModelViewSet):
    queryset = XForm.objects.all()
    serializer_class = XFormSerializer
