import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SocialProjectDemo.settings")

import django
django.setup()

from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from SocialProjectDemo.middleware import JwtCookieMiddleware
from events.routing import websocket_urlpatterns 
django_asgi_app = ASGIStaticFilesHandler(get_asgi_application())

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtCookieMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})