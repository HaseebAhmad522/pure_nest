import logging
import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import OTPVerification

logger = logging.getLogger(__name__)

__all__ = ["EmailDeliveryError", "create_otp_for_user", "verify_otp"]

SITE_NAME = "Pure Nest"


class EmailDeliveryError(Exception):
    """Raised when a verification email could not be sent."""


def generate_otp(length=6):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def send_verification_email(user, token):
    if not user.email:
        raise EmailDeliveryError("Email address is required for verification.")

    context = {
        "user": user,
        "token": token,
        # expiry removed: OTPs do not expire
        "site_name": SITE_NAME,
    }

    subject = f"Verify your {SITE_NAME} account"
    text_content = render_to_string("users/emails/verification_email.txt", context)
    html_content = render_to_string("users/emails/verification_email.html", context)

    try:
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        logger.info("Verification email sent to %s", user.email)
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", user.email, exc)
        raise EmailDeliveryError(f"Failed to send verification email: {exc}") from exc


def create_otp_for_user(user):
    OTPVerification.objects.filter(user=user, is_verified=False).update(
        is_verified=True
    )

    otp_code = generate_otp()
    # Do not set an expiry; OTPs will remain valid until verified
    otp_record = OTPVerification.objects.create(user=user, otp=otp_code)
    send_verification_email(user, otp_code)
    return otp_record


def verify_otp(user, otp_code):
    otp_record = (
        OTPVerification.objects.filter(
            user=user,
            otp=otp_code,
            is_verified=False,
        )
        .order_by("-created_at")
        .first()
    )

    if not otp_record:
        return False, "Invalid verification token."

    otp_record.is_verified = True
    otp_record.verified_at = timezone.now()
    otp_record.save(update_fields=["is_verified", "verified_at"])
    return True, otp_record
