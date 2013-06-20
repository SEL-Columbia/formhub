from rest_framework import viewsets
from api.serializers import UserProfileSerializer
from main.models import UserProfile


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
