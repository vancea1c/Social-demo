
import random
import string

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from Profile.models import Profile, GENDER_CHOICES

import datetime

from accounts.validators import StrongPasswordValidator
from accounts.validators import UsernameValidator
from accounts.utils import get_user_or_error

User = get_user_model()
    
class PasswordValidationMixin:
    def _validate_strong_password(self, value: str) -> str:
        validator = StrongPasswordValidator()
        try:
            validator.validate(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate_password(self, value: str) -> str:
        return self._validate_strong_password(value)

    def validate_newPassword(self, value: str) -> str:
        return self._validate_strong_password(value)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email']
        read_only_fields=['id', 'username']


class ForgotPwRequestSerializer( serializers.Serializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "blank":    "Username or Email is required.1",
            "required": "Username or Email is required.2",
        },
    )
    
    def validate(self, attrs):
        identifier_value = attrs.get("identifier", "").strip()
        user = get_user_or_error(identifier_value, field_name="identifier")
        self.user = user
        return attrs
    
    def save(self):
        user = self.user
        # generează cod și îl stochează în cache
        code = "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )
        cache_key = f"pw_reset_{user.id}"
        cache.set(cache_key, code, 300)  # 5 minute
        # trimite email
        subject = "Password Reset Code"
        message = (
            f"Hello {user.username},\n\n"
            f"Here is your password reset code: {code}\n"
            "This code is valid for 5 minutes."
        )
        send_mail(
            subject,
            message,
            "social.project1304@gmail.com",
            [user.email],
            fail_silently=False,
        )
        return code


class ForgotPwVerifySerializer( serializers.Serializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "blank":    "Username or Email is required.1",
            "required": "Username or Email is required.2",
        },
    )
    code = serializers.CharField(required=True)

    def validate(self, attrs):
        identifier_value = attrs.get("identifier", "").strip()
        code = attrs["code"].strip()
        user = get_user_or_error(identifier_value, field_name="identifier")

        # compară codul cu cel din cache
        cache_key = f"pw_reset_{user.id}"
        real_code = cache.get(cache_key)
        if real_code is None:
            raise ValidationError({"code": "Reset code expired."})
        if code != real_code:
            raise ValidationError({"code": "Incorrect code."})

        attrs["user"] = user
        return attrs
    
class ResetPasswordSerializer( PasswordValidationMixin, serializers.Serializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "blank":    "Username or Email is required.",
            "required": "Username or Email is required.",
        },
    )
    code = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "blank":    "Reset code is required.",
            "required": "Reset code is required.",
        },
    )
    newPassword = serializers.CharField(
        required=True,
        write_only=True,
        error_messages={
            "blank":    "New password is required.",
            "required": "New password is required.",
        },
    )
    
    def validate(self, attrs):
        code= attrs["code"].strip()
        
        identifier_value = attrs.get("identifier", "").strip()
        user = get_user_or_error(identifier_value, field_name="identifier")

        cache_key = f"pw_reset_{user.id}"
        real_code = cache.get(cache_key)
        if real_code is None:
            raise ValidationError({"code": "Reset code expired."})
        if code != real_code:
            raise ValidationError({"code": "Incorrect code."})

        attrs["user"] = user
        return attrs
    
    def validate_newPassword(self, value: str) -> str:
        return self._validate_strong_password(value)


    def save(self):
        user = self.validated_data["user"]
        new_pw = self.validated_data["newPassword"]
        # schimbă parola și salvează
        user.set_password(new_pw)
        user.save()

        # invalidează codul în cache
        cache_key = f"pw_reset_{user.id}"
        cache.delete(cache_key)

        return user

class SignInSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "blank":    "Username or Email is required.1",
            "required": "Username or Email is required.2",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        error_messages={
            "blank":    "Password is required.",
            "required": "Password is required.",
        },
    )
    def validate(self, attrs):
        identifier_value = attrs.get("identifier", "").strip()
        password = attrs.get("password")

        try:
            self.user = get_user_or_error(identifier_value, field_name="identifier")
        except ValidationError as e:
            raise

        errors = {}
        if not identifier_value and not password:
            errors["non_field_errors"] = "Username/Email and password are required."
        elif not identifier_value:
            errors["identifier"] = "Username or Email is required."
        elif not password:
            errors["password"] = "Password is required."
        if errors:
            raise ValidationError(errors)

        authenticated_user = authenticate(
            username=self.user.username,
            password=password
        )
        if authenticated_user is None:
            raise ValidationError({"password": "Incorrect password."})

        attrs["user"] = authenticated_user
        return attrs

class SignUpSerializer(PasswordValidationMixin, serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    gender = serializers.ChoiceField(choices=GENDER_CHOICES, required=True)
    birth_date = serializers.DateField(required=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "gender",
            "birth_date",
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {
                "error_messages": {
                    "blank": "Email is required.",
                    "invalid": "Enter a valid email.",
                }
            },
        }

    def validate_username(self, value):
        validator = UsernameValidator()
        try:
            validator.validate(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate_birth_date(self, value):
        today = datetime.date.today()

        age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )
        if age < 18:
            raise serializers.ValidationError("You must be at least 18 years old.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        gender = validated_data.pop("gender", None)
        birth_date = validated_data.pop("birth_date", None)

        user = User.objects.create_user(**validated_data)

        if gender is not None:
            user.profile.gender = gender
        if birth_date is not None:
            user.profile.birth_date = birth_date
        user.profile.save()
        return user
    
class PasswordChangeSerializer(PasswordValidationMixin, serializers.Serializer):
    password = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False,
    )

    newPassword = serializers.CharField(
        required=True,
        write_only=True,
        trim_whitespace=False,
    )
    
    def validate_password(self, value:str)->str:
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        
        if user is None or not user.is_authenticated:
            raise ValidationError("Authentication credentials were not provided.")
        
        if not user.check_password(value):
            raise serializers.ValidationError("The current (old) password is incorrect.")
        return value
    
    def validate_newPassword(self, value: str) -> str:
        return self._validate_strong_password(value)
    
    def save(self, **kwargs):
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("Authentication credentials were not provided.")
        
        new_pw = self.validated_data["newPassword"]
        if user.check_password(new_pw):
            raise ValidationError({"newPassword": "New password must be different from the old one."})
        user.set_password(new_pw)
        user.save()
        return user
