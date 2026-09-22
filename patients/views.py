from rest_framework import generics
from users.permissions import IsPatient

from .models import PatientProfile
from .serializers import PatientProfileSerializer


class PatientProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = PatientProfileSerializer
    permission_classes = [IsPatient]

    def get_object(self):

        profile, created = PatientProfile.objects.get_or_create(
            user=self.request.user, defaults={"full_name": self.request.user.email}
        )

        return profile
