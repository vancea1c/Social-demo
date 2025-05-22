from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import include, path
from .views import PostViewSet

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

urlpatterns = [
    path("", include(router.urls)),
]
