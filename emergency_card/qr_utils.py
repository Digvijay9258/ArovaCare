import qrcode

from django.conf import settings


def get_emergency_url(emergency_token):
    """
    Generate the public emergency-card URL.

    The URL must match the Django route:

        /api/emergency-card/<token>/
    """

    base_url = getattr(
        settings,
        "AROVA_CARE_PUBLIC_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    return f"{base_url}" f"/api/emergency-card/" f"{emergency_token}/"


def generate_emergency_qr(emergency_token):
    """
    Generate a QR code containing only the secure
    emergency-card URL.

    No medical information is stored inside the QR code.
    """

    emergency_url = get_emergency_url(emergency_token)

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )

    qr.add_data(emergency_url)

    qr.make(fit=True)

    return qr.make_image()
