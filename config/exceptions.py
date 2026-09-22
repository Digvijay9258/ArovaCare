from django.conf import settings

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def arova_exception_handler(exc, context):
    """
    Centralized exception handler for Arova APIs.

    Keeps normal DRF validation/authentication responses
    while preventing unexpected internal errors from exposing
    sensitive implementation details.
    """

    response = exception_handler(
        exc,
        context,
    )

    if response is not None:
        return response

    # ---------------------------------------------------------
    # Unexpected server-side exception
    # ---------------------------------------------------------

    if settings.DEBUG:
        return Response(
            {
                "detail": ("An unexpected error occurred."),
                "error_type": exc.__class__.__name__,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"detail": ("An unexpected error occurred. " "Please try again later.")},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
