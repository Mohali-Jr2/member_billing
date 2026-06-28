from .models import AuditLog


def log_action(request, action, obj=None, object_type="", object_id="", object_repr="", details=""):
    if obj is not None:
        object_type = object_type or obj.__class__.__name__
        object_id = object_id or str(getattr(obj, "pk", ""))
        object_repr = object_repr or str(obj)

    user = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        user = None

    AuditLog.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        object_repr=object_repr[:255],
        details=details,
        ip_address=_client_ip(request),
    )


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None
