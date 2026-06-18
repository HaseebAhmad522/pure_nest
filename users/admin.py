from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, OTPVerification


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "mobile_number",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_mobile_verified",
        "is_active",
    )
    list_filter = ("role", "is_mobile_verified", "is_active")
    search_fields = ("mobile_number", "first_name", "last_name", "email")
    ordering = ("mobile_number",)
    fieldsets = (
        (None, {"fields": ("mobile_number", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "address",
                    "latitude",
                    "longitude",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_mobile_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "mobile_number",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                ),
            },
        ),
    )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "is_verified", "created_at", "expires_at", "verified_at")
    list_filter = ("is_verified",)
    search_fields = ("user__mobile_number", "otp")
