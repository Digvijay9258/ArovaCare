from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):

    message = "Only patients can manage medical access."

    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "PATIENT"
        )