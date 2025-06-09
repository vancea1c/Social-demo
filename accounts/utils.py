import re
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

def get_user_or_error(identifier: str, field_name: str):
    ident = identifier.strip()
    if "@" in ident:
        try:
            user = User.objects.get(email__iexact=ident)
        except User.DoesNotExist:
            raise ValidationError({field_name: "This email does not exist in our system."})
    else:
        try:
            user = User.objects.get(username=ident)
        except User.DoesNotExist:
            raise ValidationError({field_name: "This username does not exist in our system."})
    return user