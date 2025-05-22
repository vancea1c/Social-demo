from rest_framework import viewsets, permissions, status, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Profile
from .serializers import ProfileSerializer
from .permissions import IsOwnerOrReadOnly
from django.db.models import Q
from django.shortcuts import get_object_or_404


class ProfileViewSet(viewsets.ModelViewSet):
    """
    - GET    /api/profile/       → listează (în cazul nostru doar profilul curent)
    - PATCH  /api/profile/{pk}/  → modifică câmpurile permise
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field       = 'user__username'   #  URL /api/profile/<username>/
    filter_backends = [filters.SearchFilter]
    search_fields   = ['user__username', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        user = self.request.user
        # afișează:
        #   - toate profilurile publice
        #   - + propriul profil (chiar dacă e privat)
        # excludem și blocările, dacă ai nevoie:
        return Profile.objects.filter(
            Q(is_private=False) |
            Q(user=user)
        )
        
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        profile = self.get_queryset().first()
        if not profile:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        # nu vrem retrieve pe pk diferit, redirectăm la list (care deja dă obiectul)
        return self.list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # patchează profilul curent fără să ai nevoie de pk în URL
        return super().partial_update(request, *args, **kwargs)