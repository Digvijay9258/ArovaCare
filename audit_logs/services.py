from .models import AuditLog


def create_audit_log(
    *,
    user=None,
    action,
    resource_type,
    resource_id=None,
    request=None,
    metadata=None,
):
    """
    Create an immutable audit log entry.

    Parameters:
        user:
            User who performed the action.

        action:
            AuditLog.Action value.

        resource_type:
            Type of resource affected.
            Example: "MedicalRecord", "Consent", "Appointment".

        resource_id:
            ID of the affected resource.

        request:
            Django/DRF request object.
            Used to capture IP address.

        metadata:
            Additional non-sensitive information about the action.
    """

    ip_address = None

    if request:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

    return AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=ip_address,
        metadata=metadata or {},
    )
