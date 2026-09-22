from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):

    message = "Only patients can access this resource."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "PATIENT"


class IsDoctor(BasePermission):

    message = "Only doctors can access this resource."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "DOCTOR"


class IsAdminUserRole(BasePermission):

    message = "Only administrators can perform this action."

    def has_permission(self, request, view):

        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role == "ADMIN"
        )
