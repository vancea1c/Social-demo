from django.db import transaction
from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .serializers import (
    PasswordChangeSerializer, SignInSerializer, SignUpSerializer,
    ForgotPwRequestSerializer, ForgotPwVerifySerializer, ResetPasswordSerializer, UserSerializer
)
from Profile.models import Profile
from Posts.models import Post

class AccountMeView(APIView):
    """
    GET  /api/accounts/me/    --> return the authenticated user's data
    DELETE /api/accounts/me/   --> delete the authenticated user's account
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        user = request.user

        for outstanding_token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding_token)
        try:
            profile = Profile.objects.filter(user=user).first() 
        except Profile.DoesNotExist:
            profile = None
        
        if profile:
            if profile.profile_image and profile.profile_image.name != "profile_images/default.jpg":
                 profile.profile_image.delete(save=False)
            if profile.cover_image:
                profile.cover_image.delete(save=False)
                
        for post in Post.objects.filter(author=user):
            for media in post.posted_media.all():
                if media.file:
                    media.file.delete(save=False) 
                media.delete()
                
                
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class MyTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data
        
        resp = Response(tokens, status=200)
        
        resp.set_cookie(
            key="access_token",
            value=tokens["access"],
            httponly=True,
            secure=True,
            samesite="None",
            path="/",
        )
        return resp

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
        serializer = self.get_serializer(data=request.data, )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        
        
        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        resp = Response(
            {
                "message": "Authentication successful.",
                "user_id": user.id,
                "access": str(access),
                "refresh": str(refresh),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
            }, status=status.HTTP_200_OK)
        resp.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=False,       
            samesite="Lax",
            path="/",
        )
        return resp

class PasswordChangeView(generics.GenericAPIView):
    serializer_class=PasswordChangeSerializer
    permission_classes =[IsAuthenticated]
    
    def post (self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


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
