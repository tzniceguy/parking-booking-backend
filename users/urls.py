from django.urls import path
from .views import MotoristRegistrationView, MotoristLoginView, OperatorRegisterView, OperatorLoginView,     UserProfileView, OTPVerificationView, ResendOTPView, CurrentUserView

urlpatterns = [
    path('register/',MotoristRegistrationView.as_view(), name= "motorist-register" ),
    path('verify-otp/', OTPVerificationView.as_view(), name="verify-otp"),
    path('resend-otp/', ResendOTPView.as_view(), name="resend-otp"),
    path('login/', MotoristLoginView.as_view(), name = "motorist-login"),
    path('operator-register/', OperatorRegisterView.as_view(), name="operator-login"),
    path('operator-login/', OperatorLoginView.as_view(), name = "operator-login"),
    path('profile/', UserProfileView.as_view(), name="user-profile"),
    path('profile/me/', CurrentUserView.as_view(), name="current-user-profile"),
]
