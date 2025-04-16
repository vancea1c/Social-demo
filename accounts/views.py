from email import message
from math import e
from django.shortcuts import render
from django.contrib.auth.models import User

from python_utils import raise_exception
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework import status

from .serializers import SignUpSerializer
from .serializers import SignInSerializer
from .serializers import ForgotPwSerializer

# Create your views here.


class ForgotPwView(generics.GenericAPIView):
    serializer_class = ForgotPwSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.send_reset_code()
            return Response({"message": "Email was sent"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignUpApiView(generics.GenericAPIView):
    serializer_class = SignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "Cont creat cu succes", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class SignInApiView(generics.GenericAPIView):
    serializer_class = SignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Authentication successful.",
                "user_id": user.id,
                "token": token.key,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
            }
        )


# views.py


@api_view(["GET"])
def check_username(request):
    username = request.query_params.get("username", "")
    exists = User.objects.filter(username=username).exists()
    return Response({"available": not exists})


@api_view(["GET"])
def check_email(request):
    email = request.query_params.get("email", "")
    exists = User.objects.filter(email=email).exists()
    return Response({"available": not exists})
