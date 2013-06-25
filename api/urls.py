from rest_framework import routers
from api import views as api_views


router = routers.DefaultRouter()
router.register(r'users', api_views.UserProfileViewSet)
router.register(r'u', api_views.UserViewSet)
router.register(r'forms', api_views.XFormViewSet)
router.register(r'projects', api_views.ProjectViewSet)
