from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    - Dacă profilul e blocat (în oricare sens), nu lași niciun request treacă.
    - GET/HEAD/OPTIONS: oricine (cu excepția blocărilor și profilurilor private).
    - POST/PUT/PATCH/DELETE: doar proprietarul.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user

        # --- 1) verificăm blocările ---
        # proprietarul profilului te-a blocat?
        if user in obj.blocked_users.all():
            return False

        # tu l-ai blocat pe proprietar?
        # (atenție: presupunem că există mereu un Profile pentru user)
        try:
            your_profile = user.profile
        except AttributeError:
            your_profile = None

        if your_profile and obj.user in your_profile.blocked_users.all():
            return False

        # --- 2) acces de citire ---
        if request.method in SAFE_METHODS:
            # dacă e privat, doar proprietarul
            if getattr(obj, 'is_private', False) and obj.user != user:
                return False
            return True

        # --- 3) acces de modificare ---
        return obj.user == user
