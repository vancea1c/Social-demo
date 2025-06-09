from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet

app_name = 'Profile_api'

router = DefaultRouter()
router.register(r'', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]
