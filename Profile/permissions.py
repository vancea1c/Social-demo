from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user in obj.blocked_users.all():
            return False

        try:
            your_profile = user.profile
        except AttributeError:
            your_profile = None

        if your_profile and obj.user in your_profile.blocked_users.all():
            return False

        if request.method in SAFE_METHODS:
            if getattr(obj, 'is_private', False) and obj.user != user:
                return False
            return True
        return obj.user == user
