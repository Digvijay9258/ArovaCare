from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import SecuritySession


class ArovaJWTAuthentication(JWTAuthentication):
    """
    Arova JWT authentication with SecuritySession validation.

    Every JWT must contain a valid session_id.
    The corresponding SecuritySession must be active.
    Deactivated users are not allowed to authenticate.
    """

    def authenticate(self, request):

        result = super().authenticate(request)

        if result is None:
            return None

        user, validated_token = result

        # ---------------------------------------------------------
        # USER ACCOUNT STATUS CHECK
        # ---------------------------------------------------------
        if not user.is_active:
            raise AuthenticationFailed("This user account has been deactivated.")

        # ---------------------------------------------------------
        # SECURITY SESSION CHECK
        # ---------------------------------------------------------
        session_id = validated_token.get("session_id")

        if not session_id:
            raise AuthenticationFailed("Security session information is missing.")

        security_session = SecuritySession.objects.filter(
            user=user,
            session_token_id=session_id,
        ).first()

        if not security_session:
            raise AuthenticationFailed("Security session not found.")

        if not security_session.is_active:
            raise AuthenticationFailed("This security session has been logged out.")

        # ---------------------------------------------------------
        # UPDATE LAST ACTIVITY
        # ---------------------------------------------------------
        security_session.save(update_fields=["last_activity"])

        return user, validated_token
