from rest_framework.permissions import BasePermission


class IsDoctor(BasePermission):
    message = "Only doctors can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "DOCTOR"
        )


class IsPatient(BasePermission):
    message = "Only patients can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "PATIENT"
        )
