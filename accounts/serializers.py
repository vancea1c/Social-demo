import email
import random
import string

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from Profile.models import Profile, GENDER_CHOICES

import datetime
from dataclasses import fields

from accounts.validators import StrongPasswordValidator
from accounts.validators import UsernameValidator


class ForgotPwSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(
        required=True,
        allow_blank=False,  # important pentru eroarea "blank"
        error_messages={
            "blank": "Username or Email is required.",
            "required": "Username or Email is required.",
        }
    )

    class Meta:
        model = User
        fields = ["identifier"]

    def validate(self, data):
        identifier = data.get("identifier", "").strip()
        errors = {}

        if not identifier:
            errors["identifier"] = "Username or Email is required."
        if errors:
            raise ValidationError(errors)

        if "@" in identifier:
            try:
                user_obj = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise ValidationError(
                    {"identifier": "This email does not exit in our system."}
                )
        else:
            try:
                user_obj = User.objects.get(username=identifier)
            except User.DoesNotExist:
                raise ValidationError(
                    {"identifier": "This username does not exit in our system."}
                )

        data["user"] = user_obj
        return data

    def send_reset_code(self):
        code = "".join(random.choices(string.ascii_letters + string.digits, k=6))
        user_obj = self.validated_data["user"]

        # Stocăm codul în cache (valabil 5 minute, de exemplu)
        cache_key = f"pw_reset_{user_obj.id}"
        cache.set(cache_key, code, 300)

        subject = "Password Reset Code"
        message = (
            f"Hello {user_obj.username},\n\n"
            f"Here is your password reset code: {code}\n"
            "This code is valid for 5 minutes."
        )
        from_email = "social.project1304@gmail.com"
        recipient_list = [user_obj.email]

        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return code


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
