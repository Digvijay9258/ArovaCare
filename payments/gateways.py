import razorpay

from django.conf import settings


class RazorpayGateway:
    """
    Razorpay gateway helper.

    This class is responsible only for communication with Razorpay.
    Payment status is still controlled by our payment service and
    verified webhook flow.
    """

    def __init__(self):
        if not settings.RAZORPAY_KEY_ID:
            raise ValueError("RAZORPAY_KEY_ID is not configured.")

        if not settings.RAZORPAY_KEY_SECRET:
            raise ValueError("RAZORPAY_KEY_SECRET is not configured.")

        self.client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

    def create_order(
        self,
        *,
        amount,
        currency="INR",
        receipt=None,
        notes=None,
    ):
        """
        Create a Razorpay order.

        Razorpay expects amount in the smallest currency unit.
        For INR this means paise.
        """

        amount_in_paise = int(round(float(amount) * 100))

        payload = {
            "amount": amount_in_paise,
            "currency": currency,
        }

        if receipt:
            payload["receipt"] = receipt

        if notes:
            payload["notes"] = notes

        return self.client.order.create(data=payload)

    def verify_payment_signature(
        self,
        *,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ):
        """
        Verify Razorpay checkout payment signature.
        """

        self.client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        return True

    def verify_webhook_signature(
        self,
        *,
        payload,
        signature,
    ):
        """
        Verify Razorpay webhook signature.

        The payload must be the exact raw request body.
        """

        if not settings.RAZORPAY_WEBHOOK_SECRET:
            raise ValueError("RAZORPAY_WEBHOOK_SECRET is not configured.")

        self.client.utility.verify_webhook_signature(
            payload,
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )

        return True
