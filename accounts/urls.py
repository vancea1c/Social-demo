# accounts/urls.py
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .views import (
    CheckEmailView,
    CheckUsernameView,
    SignInApiView,
    SignUpApiView,
    ForgotPasswordView,
    VerifyResetCodeView,
    ResetPasswordView,
    GetUserView
)

app_name = 'accounts_api'

@api_view(['GET'])
@permission_classes([AllowAny]) 
def api_root(request, format=None):
    """
    Returnează un JSON cu link-uri către toate sub-rutele din /api/accounts/.
    """
    return Response({
        'sign_up':        reverse('accounts_api:sign_up',        request=request, format=format),
        'sign_in':        reverse('accounts_api:sign_in',        request=request, format=format),
        'check-username': reverse('accounts_api:check-username', request=request, format=format),
        'check-email':    reverse('accounts_api:check-email',    request=request, format=format),
        'forgot_password':      reverse('accounts_api:forgot-password',    request=request, format=format),
        'verify_reset_code':    reverse('accounts_api:verify-reset-code', request=request, format=format),
        'reset_password':       reverse('accounts_api:reset-password',    request=request, format=format),
        'me/':                  reverse('accounts_api:accounts-me', request=request, format=format)
    })

urlpatterns = [
    # 1) index pe rădăcină
    path('',                         api_root,                name='accounts-root'),

    # 2) restul endpoint-urilor
    path('sign_up/',      SignUpApiView.as_view(),      name='sign_up'),
    path('sign_in/',      SignInApiView.as_view(),      name='sign_in'),
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
    path('check-email/',    CheckEmailView.as_view(),    name='check-email'),
    path('forgot-password/',    ForgotPasswordView.as_view(),    name='forgot-password'),
    path('verify-reset-code/',  VerifyResetCodeView.as_view(),  name='verify-reset-code'),
    path('reset-password/',     ResetPasswordView.as_view(),     name='reset-password'),
    path('me/', GetUserView.as_view(), name='accounts-me'),
]
