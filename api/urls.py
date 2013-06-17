from rest_framework import routers
from api import views as api_views


router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'profiles', api_views.UserProfileViewSet)
router.register(r'groups', api_views.GroupViewSet)
