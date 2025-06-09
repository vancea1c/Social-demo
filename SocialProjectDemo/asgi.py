import os

# 1) set the settings module **first**
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SocialProjectDemo.settings")

# 2) now initialize Django
import django
django.setup()

# 3) import ASGI handler and static‐files support
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

# 4) import Channels routing & middleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from Posts.middleware import JwtCookieMiddleware
import Posts.routing  # make sure this import comes *after* django.setup()

# wrap the Django application to serve static files
django_asgi_app = ASGIStaticFilesHandler(get_asgi_application())

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        OriginValidator(
            JwtCookieMiddleware(
                URLRouter(Posts.routing.websocket_urlpatterns)
            ),
            # only allow your frontend origin:
            ["http://localhost:5173"]
        )
    ),
})
