from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from rest_framework.authtoken.models import Token


class AllowInactiveUserTokenAuthentication(TokenAuthentication):
    """TokenAuthentication variant that does not reject inactive users.

    Use carefully: this only relaxes the `is_active` check so endpoints
    can be reached when a user row has `is_active=False` or NULL.
    """

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.select_related("user").get(key=key)
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token.")

        user = token.user
        if user is None:
            raise exceptions.AuthenticationFailed("User inactive or deleted.")

        # Intentionally do NOT check user.is_active here.
        return (user, token)
