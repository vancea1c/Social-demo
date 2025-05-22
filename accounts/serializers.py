import email
import random
import string

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.cache import cache
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from Profile.models import Profile, GENDER_CHOICES

import datetime
from dataclasses import fields

from accounts.validators import StrongPasswordValidator
from accounts.validators import UsernameValidator

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email']
        read_only_fields=['id', 'username']


class ForgotPwRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            "blank":    "Username or Email is required.",
            "required": "Username or Email is required.",
        },
    )

    def validate_identifier(self, value):
        value = value.strip()
        if "@" in value:
            try:
                user = User.objects.get(email=value)
            except User.DoesNotExist:
                raise ValidationError("This email does not exist in our system.")
        else:
            try:
                user = User.objects.get(username=value)
            except User.DoesNotExist:
                raise ValidationError("This username does not exist in our system.")
        self.context["user"] = user
        return value

    def save(self):
        user = self.context["user"]
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


class ForgotPwVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    code = serializers.CharField(required=True)

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        code = attrs["code"].strip()

        # găsește user-ul
        if "@" in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise ValidationError({"identifier": "Unknown email."})
        else:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                raise ValidationError({"identifier": "Unknown username."})

        # compară codul cu cel din cache
        cache_key = f"pw_reset_{user.id}"
        real_code = cache.get(cache_key)
        if real_code is None:
            raise ValidationError({"code": "Reset code expired."})
        if code != real_code:
            raise ValidationError({"code": "Incorrect code."})

        attrs["user"] = user
        return attrs
    
class ResetPasswordSerializer(serializers.Serializer):
    identifier  = serializers.CharField(required=True)
    code        = serializers.CharField(required=True)
    newPassword = serializers.CharField(required=True, write_only=True)

    def validate_newPassword(self, value: str) -> str:
        validator = StrongPasswordValidator()
        try:
            validator.validate(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        identifier  = attrs["identifier"].strip()
        code        = attrs["code"].strip()
        new_pw      = attrs["newPassword"]

        # 1️⃣ găsește user-ul după identifier
        if "@" in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise ValidationError({"identifier": "Unknown email."})
        else:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                raise ValidationError({"identifier": "Unknown username."})

        # 2️⃣ verifică codul în cache
        cache_key = f"pw_reset_{user.id}"
        real_code = cache.get(cache_key)
        if real_code is None:
            raise ValidationError({"code": "Reset code expired."})
        if code != real_code:
            raise ValidationError({"code": f"Incorrect code. {real_code}"})

        # 3️⃣ toate bune → atașăm user și vom șterge codul
        attrs["user"] = user
        return attrs

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
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier", "").strip()
        password = attrs.get("password")

        errors = {}
        if not identifier and not password:
            errors["non_field_errors"] = "Username/Email and password are required."
        elif not identifier:
            errors["identifier"] = "Username or Email is required."
        elif not password:
            errors["password"] = "Password is required."
        if errors:
            raise ValidationError(errors)

        if "@" in identifier:
            try:
                user_obj = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise ValidationError(
                    {"identifier": "This email does not exist in our system."}
                )
            username = user_obj.username
        else:
            username = identifier
            if not User.objects.filter(username=username).exists():
                raise ValidationError(
                    {"identifier": "This username does not exist in our system."}
                )

        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError({"password": "Incorrect password."})

        attrs["user"] = user
        return attrs


class SignUpSerializer(serializers.ModelSerializer):
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

    def validate_password(self, value):
        validator = StrongPasswordValidator()
        try:
            validator.validate(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered")
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
