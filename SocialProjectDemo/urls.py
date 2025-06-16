from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import health_check  

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/accounts/', include('accounts.urls', namespace='accounts_api')),
    path('api/profile/',  include('Profile.urls', namespace='profile_api')),
    path('api/token/',    TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('Posts.urls')),
    path("health/", health_check),
    path('api/', include('Notifications.urls')),
    path('api/', include('Friendship.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
