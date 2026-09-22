from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Allows access only to authenticated Arova Admin users.
    """

    message = "Admin access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )
