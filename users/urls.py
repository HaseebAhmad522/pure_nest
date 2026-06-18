from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    OTPVerificationViewSet,
    UserProfileViewSet,
    SignupViewSet,
    LoginViewSet,
    SendOTPViewSet,
    VerifyOTPViewSet,
    ForgotPasswordViewSet,
    ResetPasswordViewSet,
    UserProfileViewSet
)

# router = DefaultRouter()
# router.register("users", CustomUserViewSet, basename="user")
# router.register("otp-verifications", OTPVerificationViewSet, basename="otp-verification")
# router.register("user-profile", UserProfileViewSet, basename="user-profile")

urlpatterns = [
    # CRUD and read-only endpoints via router
    # path("", include(router.urls)),

    # Individual auth endpoints implemented as ModelViewSet.create mapped to POST
    path("users/signup/", SignupViewSet.as_view({"post": "create"}), name="users-signup"),
    path("users/login/", LoginViewSet.as_view({"post": "create"}), name="users-login"),
    path("users/send-otp/", SendOTPViewSet.as_view({"post": "create"}), name="users-send-otp"),
    path("users/verify-otp/", VerifyOTPViewSet.as_view({"post": "create"}), name="users-verify-otp"),
    path("users/forgot-password/", ForgotPasswordViewSet.as_view({"post": "create"}), name="users-forgot-password"),
    path("users/reset-password/", ResetPasswordViewSet.as_view({"post": "create"}), name="users-reset-password"),
    path("users/profile/", UserProfileViewSet.as_view({"get": "retrieve", "put": "update"}), name="users-profile"),
]
