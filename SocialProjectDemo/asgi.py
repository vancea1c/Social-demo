# asgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SocialProjectDemo.settings")
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


# get your normal ASGI handler…
django_asgi_app = get_asgi_application()
# …and wrap it so it intercepts STATIC_URL for you
django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        # IMPORTA rutarea DOAR AICI (nu sus de tot în fișier!)
        URLRouter(
            __import__("Posts.routing").routing.websocket_urlpatterns
        )
    ),
})