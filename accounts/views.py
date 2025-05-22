from argparse import Action
from email import message
from math import e
from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, action
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from Profile import serializers

from .serializers import (
    SignInSerializer, SignUpSerializer,
    ForgotPwRequestSerializer, ForgotPwVerifySerializer, ResetPasswordSerializer, UserSerializer
)
class GetUserView(generics.RetrieveAPIView):
    serializer_class=UserSerializer
    permission_classes=([IsAuthenticated])
    
    def get_object(self):
        return self.request.user



# Create your views here.
class ForgotPasswordView(generics.GenericAPIView):
    serializer_class=ForgotPwRequestSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # trimite codul
        return Response({"detail": "Reset code sent."})

class VerifyResetCodeView(generics.GenericAPIView):
    serializer_class=ForgotPwVerifySerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Code verified."})
    
class ResetPasswordView(generics.GenericAPIView):
    serializer_class= ResetPasswordSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Parola a fost schimbată cu succes."},
            status=status.HTTP_200_OK
        )


class SignUpApiView(generics.GenericAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token
        return Response(
            {"message": "Cont creat cu succes", 
             "user_id": user.id,
             "access": str(access),
             "refresh": str(refresh),
             },status=status.HTTP_201_CREATED)


class SignInApiView(generics.GenericAPIView):
    serializer_class = SignInSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        
        
        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        return Response(
            {
                "message": "Authentication successful.",
                "user_id": user.id,
                "access": str(access),
                "refresh": str(refresh),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
            }
        )


# views.py


class CheckUsernameView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        username = request.query_params.get("username", "")
        exists = User.objects.filter(username=username).exists()
        return Response({"available": not exists})

class CheckEmailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        email = request.query_params.get("email", "")
        exists = User.objects.filter(email=email).exists()
        return Response({"available": not exists})
