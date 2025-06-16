from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from .models import FriendRequest
from Profile.models import Profile
from .serializers import FriendRequestSerializer
from events.utils import send_real_time
from django.contrib.auth.models import User

def broadcast_friend_request(instance: FriendRequest, event_type: str, request=None):
    for user in [instance.from_user, instance.to_user]:
        context = {"request": request}
        data = FriendRequestSerializer(instance, context=context).data
        data["type"] = event_type
        

        send_real_time(
            event_type="friend_request",
            recipient_group=f"user_{user.id}",
            data=data
        )

class FriendRequestViewSet(viewsets.ModelViewSet):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(
            active=True
        ).filter(
            Q(from_user=user) | Q(to_user=user)
        )

    def perform_create(self, serializer):
        from_user = self.request.user
        to_user = serializer.validated_data['to_user']

        existing = FriendRequest.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).order_by('-created_at').first()

        if existing:
            if existing.active:
                raise ValidationError("Friend request already exists.")
            else:
                existing.active = True
                existing.status = FriendRequest.STATUS_PENDING
                existing.save()
                broadcast_friend_request(existing, "new", request=self.request)
                return Response(
                    FriendRequestSerializer(existing, context={"request": self.request}).data,
                    status=status.HTTP_200_OK
                )

        instance = serializer.save(from_user=from_user)
        broadcast_friend_request(instance, "new", request=self.request)
        return Response(
            FriendRequestSerializer(instance, context={"request": self.request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'])
    def accept(self, request, pk=None):
        instance = self.get_object()
        if instance.to_user != request.user:
            return Response({"error": "Not yours to accept."}, status=403)
        instance.status = FriendRequest.STATUS_ACCEPTED
        instance.active = False
        instance.save()
        broadcast_friend_request(instance, "accepted", request=request)

        return Response({"status": "accepted"})

    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        if instance.to_user != request.user:
            return Response({"error": "Not yours to reject."}, status=403)

        instance.status = FriendRequest.STATUS_REJECTED
        instance.active = False
        instance.save()
        broadcast_friend_request(instance, "rejected", request=request)

        return Response({"status": "rejected"})

    @action(detail=True, methods=['delete'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        if instance.from_user != request.user:
            return Response({"error": "Not yours to cancel."}, status=403)

        instance.active = False
        instance.save()
        broadcast_friend_request(instance, "cancelled", request=request)

        return Response({"status": "cancelled"})
    
    @action(detail=False, methods=['post'])
    def remove(self, request):
        target_username = request.data.get("username")
        if not target_username:
            return Response({"error": "Username is required"}, status=400)

        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        from_profile = request.user.profile
        to_profile = target_user.profile

        from_profile.friends.remove(to_profile)
        to_profile.friends.remove(from_profile)

        FriendRequest.objects.filter(
            Q(from_user=request.user, to_user=target_user) |
            Q(from_user=target_user, to_user=request.user),
            status=FriendRequest.STATUS_ACCEPTED
        ).delete()

        dummy_instance = FriendRequest(from_user=request.user, to_user=target_user)
        broadcast_friend_request(dummy_instance, "removed", request=request)

        return Response({"status": "removed"})

    @action(detail=False, methods=['get'])
    def mine(self, request):
        user = request.user
        sent = FriendRequest.objects.filter(from_user=user, active=True)
        received = FriendRequest.objects.filter(to_user=user, active=True)
        serializer_context = {"request": self.request}
        return Response({
            "sent": FriendRequestSerializer(sent, many=True, context=serializer_context).data,
            "received": FriendRequestSerializer(received, many=True, context=serializer_context).data,
        })