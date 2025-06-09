from rest_framework import viewsets, permissions, status, filters, mixins
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Profile
from .serializers import ProfileSerializer
from .permissions import IsOwnerOrReadOnly
from django.db.models import Q
from django.shortcuts import get_object_or_404


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    list:
        GET /api/profile/      → YOUR profile
    retrieve:
        GET /api/profile/me/   → YOUR profile
        GET /api/profile/jane/ → Jane s profile (public or your own)
    partial_update:
        PATCH /api/profile/jane/ → update *your* profile only
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field       = 'username'
    lookup_url_kwarg   = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields   = ['user__username', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        return Profile.objects.select_related('user').all()
        
    def get_object(self):
        username = self.kwargs.get(self.lookup_url_kwarg)
        if username is None:
            return get_object_or_404(Profile, user=self.request.user)
        if username == 'me':
            return get_object_or_404(Profile, user=self.request.user)
        return get_object_or_404(
            self.get_queryset(),
            user__username=username
        )