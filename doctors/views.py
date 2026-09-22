from django.db.models import Q
from rest_framework import generics

from users.permissions import IsDoctor
from users.models import User

from .models import DoctorProfile
from .serializers import (
    DoctorProfileSerializer,
    DoctorVerificationSerializer,
)
from .permissions import IsAdminUserRole


class DoctorProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = DoctorProfileSerializer
    permission_classes = [IsDoctor]

    def get_object(self):

        profile, created = DoctorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                "full_name": self.request.user.email,
                "specialization": "General Medicine",
                "medical_registration_number": (f"PENDING-{self.request.user.id}"),
            },
        )

        return profile


class DoctorVerificationView(generics.UpdateAPIView):

    queryset = DoctorProfile.objects.all()

    serializer_class = DoctorVerificationSerializer

    permission_classes = [IsAdminUserRole]

    http_method_names = ["patch"]


class DoctorListView(generics.ListAPIView):

    serializer_class = DoctorProfileSerializer

    def get_queryset(self):

        queryset = DoctorProfile.objects.filter(
            verification_status="VERIFIED"
        ).select_related("user")

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(specialization__icontains=search)
                | Q(hospital_or_clinic__icontains=search)
            )

        return queryset.order_by("full_name")
