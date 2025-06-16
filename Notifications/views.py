from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notifications
from .serializers import NotificationsSerializer


class NotificationsViewSet(
    mixins.ListModelMixin,   
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationsSerializer

    def get_queryset(self):
        # only notifications belonging to request.user
        return Notifications.objects.filter(
            to_user=self.request.user, active=True
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True) if page is not None else self.get_serializer(queryset, many=True)
        response = self.get_paginated_response(serializer.data)
        response.data['unread_count'] = self.get_queryset().filter(is_read=False).count()
        return response

    @action(detail=False, methods=['get'])
    def unread(self, request):
        qs = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True) if page is not None else self.get_serializer(qs, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        marked = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'marked': marked}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='toggle_read')
    def toggle_read(self, request, pk=None):
        notification = self.get_object() 
        notification.is_read = not notification.is_read
        notification.save(update_fields=['is_read'])
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
