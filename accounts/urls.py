from django.urls import path
from .views import (
    SignInApiView,
    SignUpApiView,
    check_username,
    check_email,
    ForgotPwView,
)

urlpatterns = [
    path("sign_up/", SignUpApiView.as_view(), name="sign_up"),
    path("sign_in/", SignInApiView.as_view(), name="sign_in"),
    path("check-username/", check_username),
    path("check-email/", check_email),
    path("forgot_password/", ForgotPwView.as_view(), name="forgot_password"),
]
