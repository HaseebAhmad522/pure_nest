from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, mobile_number, password, **extra_fields):
        if not mobile_number:
            raise ValueError("The given mobile number must be set")
        user = self.model(mobile_number=mobile_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, mobile_number=None, password=None, **extra_fields):
        # allow callers to pass mobile_number in kwargs (from serializers)
        if mobile_number is None:
            mobile_number = extra_fields.pop("mobile_number", None)
        return self._create_user(mobile_number, password, **extra_fields)

    def create_superuser(self, mobile_number=None, password=None, **extra_fields):
        if mobile_number is None:
            mobile_number = extra_fields.pop("mobile_number", None)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(mobile_number, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("rider", "Rider"),
        ("owner", "Owner"),
        ("admin", "Admin"),
    )

    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=14, unique=True, blank=True, null=True)
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="customer", blank=True, null=True
    )
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )
    is_mobile_verified = models.BooleanField(default=False, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mobile_number})"


class OTPVerification(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="otp_records",
        blank=True,
        null=True,
    )
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        mobile = self.user.mobile_number if self.user else "unknown"
        return f"{mobile} - {self.otp}"
