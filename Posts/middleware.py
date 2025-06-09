import jwt
from django.conf import settings
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

@database_sync_to_async
def get_user(validated_token):
    user = JWTAuthentication().get_user(validated_token)
    return user or AnonymousUser()

class JwtCookieMiddleware(BaseMiddleware):
    """
    Looks for our 'access_token' cookie, checks it,
    then sets scope['user'] = that user (or anonymous).
    """
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        cookie_header = headers.get(b"cookie", b"").decode()
        access_token = None
        for part in cookie_header.split(";"):
            name, *val = part.strip().split("=")
            if name == "access_token" and val:
                access_token = val[0]
                break

        if access_token:
            try:
                validated_token = JWTAuthentication().get_validated_token(access_token)
                scope["user"] = await get_user(validated_token)
            except (InvalidToken, TokenError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
