from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication

from .models import CustomUser, OTPVerification
from .serializers import (
    CustomUserSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    OTPVerificationSerializer,
    ResetPasswordSerializer,
    SendOTPSerializer,
    SignupSerializer,
    VerifyOTPSerializer,
    UserProfileSerializer,
    RiderCreateSerializer,
)
from .permissions import IsAdminRole


def get_token_for_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


class CustomUserViewSet(viewsets.ModelViewSet):
    """Standard CRUD for users. Requires token auth."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class SignupViewSet(viewsets.ModelViewSet):
    """POST /users/signup/ - create a new user (signup)."""
    queryset = CustomUser.objects.none()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Signup successful. Verification token sent to your email.",
                "user": CustomUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginViewSet(viewsets.ModelViewSet):
    """POST /users/login/ - authenticate and return token."""
    queryset = CustomUser.objects.none()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = get_token_for_user(user)
        return Response(
            {
                "message": "Login successful.",
                "token": token,
                "user": CustomUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class SendOTPViewSet(viewsets.ModelViewSet):
    """POST /users/send-otp/ - resend verification OTP."""
    queryset = CustomUser.objects.none()
    serializer_class = SendOTPSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _otp = serializer.save()
        return Response(
            {"message": "Verification token sent to your email.", "email": user.email},
            status=status.HTTP_200_OK,
        )


class VerifyOTPViewSet(viewsets.ModelViewSet):
    """POST /users/verify-otp/ - verify OTP and mark user verified."""
    queryset = CustomUser.objects.none()
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(
            {"message": "Email & Mobile Number verified successfully.", "user": CustomUserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordViewSet(viewsets.ModelViewSet):
    """POST /users/forgot-password/ - send password reset OTP."""
    queryset = CustomUser.objects.none()
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _otp = serializer.save()
        return Response(
            {"message": "Password reset token sent to your email.", "email": user.email},
            status=status.HTTP_200_OK,
        )


class ResetPasswordViewSet(viewsets.ModelViewSet):
    """POST /users/reset-password/ - reset password using OTP."""
    queryset = CustomUser.objects.none()
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "Password reset successful.", "user": CustomUserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class OTPVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OTPVerification.objects.all()
    serializer_class = OTPVerificationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class UserProfileViewSet(viewsets.ModelViewSet):
    """GET /users/profile/ - retrieve user profile. PUT /users/profile/ - update user profile."""
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Only allow updating these fields via this endpoint
        allowed_fields = {"first_name", "last_name", "address"}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"message": "Profile updated successfully.", "user": serializer.data},
            status=status.HTTP_200_OK,
        )



class AdminUserViewSet(viewsets.ViewSet):
    """Admin endpoints to manage users: list customers, list riders, create riders."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminRole]

    def list_customers(self, request):
        customers = CustomUser.objects.filter(role="customer")
        serializer = UserProfileSerializer(customers, many=True)
        return Response(serializer.data)

    def list_riders(self, request):
        riders = CustomUser.objects.filter(role="rider")
        serializer = UserProfileSerializer(riders, many=True)
        return Response(serializer.data)

    def create_rider(self, request):
        serializer = RiderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Rider created.", "user": CustomUserSerializer(user).data}, status=status.HTTP_201_CREATED)

    def list_by_role(self, request):
        """GET /admin/users/?role=customer or role=rider or role=customer,rider

        Supports repeated `role` params or comma-separated values.
        If no `role` provided, returns both customers and riders.
        """
        query_roles = request.query_params.getlist("role")
        roles = []
        for r in query_roles:
            roles.extend([x.strip() for x in r.split(",") if x.strip()])

        if not roles:
            roles = ["customer", "rider"]

        users = CustomUser.objects.filter(role__in=roles)
        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data)
    
    
    

    


