from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):

    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == "ADMIN"
        )
