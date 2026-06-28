from functools import wraps

from django.http import HttpResponseForbidden


ROLE_PATRON = "Patron"
ROLE_TREASURER = "Treasurer"
ROLE_MEMBER = "Member"


ALL_ROLES = [
    ROLE_PATRON,
    ROLE_TREASURER,
    ROLE_MEMBER,
]


CAPABILITIES = {
    "view_dashboard": [ROLE_PATRON, ROLE_TREASURER],
    "view_members": [ROLE_PATRON, ROLE_TREASURER],
    "manage_members": [ROLE_TREASURER],
    "manage_member_portal_access": [ROLE_TREASURER],
    "import_members": [ROLE_TREASURER],
    "view_payments": [ROLE_PATRON, ROLE_TREASURER],
    "record_payments": [ROLE_TREASURER],
    "request_payment_actions": [ROLE_TREASURER],
    "view_payment_actions": [ROLE_PATRON, ROLE_TREASURER],
    "approve_payment_actions": [ROLE_PATRON],
    "request_activity_funds": [ROLE_TREASURER],
    "approve_activity_funds": [ROLE_PATRON],
    "view_activity_funds": [ROLE_PATRON, ROLE_TREASURER],
    "send_reminders": [ROLE_TREASURER],
    "manage_reminder_settings": [ROLE_TREASURER],
    "view_notifications": [ROLE_TREASURER],
    "view_audit_trail": [ROLE_PATRON, ROLE_TREASURER],
    "view_reports": [ROLE_PATRON, ROLE_TREASURER],
    "export_reports": [ROLE_TREASURER],
    "manage_roles": [ROLE_PATRON],
    "view_member_portal": [ROLE_MEMBER],
}


def user_roles(user):
    if not user.is_authenticated:
        return []
    if user.is_superuser:
        return [ROLE_PATRON]

    roles = list(user.groups.filter(name__in=ALL_ROLES).values_list("name", flat=True))
    try:
        has_member_profile = bool(user.member_profile)
    except Exception:
        has_member_profile = False

    if has_member_profile and ROLE_MEMBER not in roles:
        roles.append(ROLE_MEMBER)
    return roles


def has_role(user, *roles):
    if user.is_authenticated and user.is_superuser:
        return True
    return bool(set(user_roles(user)).intersection(roles))


def has_capability(user, capability):
    return has_role(user, *CAPABILITIES.get(capability, []))


def capability_required(capability):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_capability(request.user, capability):
                return HttpResponseForbidden("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def role_context(request):
    if not hasattr(request, "user"):
        return {}
    roles = user_roles(request.user)
    return {
        "user_roles": roles,
        "role_flags": {capability: has_capability(request.user, capability) for capability in CAPABILITIES},
    }
