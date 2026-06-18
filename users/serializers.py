from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from .models import CustomUser, OTPVerification
from .utils import EmailDeliveryError, create_otp_for_user, verify_otp


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "mobile_number",
            "role",
            "address",
            "latitude",
            "longitude",
            "is_mobile_verified",
            "is_active",
            "created_at",
            "updated_at",
            "password",
        ]
        read_only_fields = ["id", "is_mobile_verified", "created_at", "updated_at"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        try:
            with transaction.atomic():
                user = CustomUser.objects.create_user(password=password, **validated_data)
                create_otp_for_user(user)
                return user
        except EmailDeliveryError as exc:
            raise serializers.ValidationError({"email": str(exc)}) from exc

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "mobile_number",
            "role",
            "address",
            "latitude",
            "longitude",
            "password",
        ]

    def validate_mobile_number(self, value):
        if CustomUser.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email address is required for verification.")
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        try:
            with transaction.atomic():
                user = CustomUser.objects.create_user(password=password, **validated_data)
                create_otp_for_user(user)
                return user
        except EmailDeliveryError as exc:
            raise serializers.ValidationError({"email": str(exc)}) from exc


class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=14)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        mobile_number = attrs.get("mobile_number")
        password = attrs.get("password")
        try:
            user = CustomUser.objects.get(mobile_number=mobile_number)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid mobile number or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid mobile number or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        # Require users to have verified their mobile/email via OTP before login
        if not user.is_mobile_verified:
            raise serializers.ValidationError(
                "Account not verified. Please verify your email token before logging in."
            )
        attrs["user"] = user
        return attrs


class SendOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=14)

    def validate_mobile_number(self, value):
        if not CustomUser.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("No user found with this mobile number.")
        return value

    def save(self):
        user = CustomUser.objects.get(mobile_number=self.validated_data["mobile_number"])
        try:
            otp_record = create_otp_for_user(user)
        except EmailDeliveryError as exc:
            raise serializers.ValidationError({"email": str(exc)}) from exc
        return user, otp_record


class VerifyOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=14)
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(mobile_number=attrs["mobile_number"])
        except CustomUser.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"mobile_number": "No user found with this mobile number."}
            ) from exc

        is_valid, result = verify_otp(user, attrs["otp"])
        if not is_valid:
            raise serializers.ValidationError({"otp": result})

        user.is_mobile_verified = True
        user.save(update_fields=["is_mobile_verified"])
        attrs["user"] = user
        attrs["otp_record"] = result
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=14)

    def validate_mobile_number(self, value):
        if not CustomUser.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("No user found with this mobile number.")
        return value

    def save(self):
        user = CustomUser.objects.get(mobile_number=self.validated_data["mobile_number"])
        try:
            otp_record = create_otp_for_user(user)
        except EmailDeliveryError as exc:
            raise serializers.ValidationError({"email": str(exc)}) from exc
        return user, otp_record


class ResetPasswordSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=14)
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(mobile_number=attrs["mobile_number"])
        except CustomUser.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"mobile_number": "No user found with this mobile number."}
            ) from exc

        is_valid, result = verify_otp(user, attrs["otp"])
        if not is_valid:
            raise serializers.ValidationError({"otp": result})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerification
        fields = [
            "id",
            "user",
            "otp",
            "is_verified",
            "created_at",
            "expires_at",
            "verified_at",
        ]
        read_only_fields = fields

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "mobile_number",
            "role",
            "address",
            "latitude",
            "longitude",
            "is_mobile_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_mobile_verified", "created_at", "updated_at"]
