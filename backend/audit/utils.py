"""
Audit logging helper for SecurFlow government compliance.
"""
from .models import AuditLog

def get_client_ip(request):
    """Extract client IP address handling proxies and reverse tunnels."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def log_audit_event(request, action, entity_type, entity_id, before_state=None, after_state=None, actor=None):
    """
    Creates an immutable audit record for compliance and tracing.
    """
    ip_address = None
    user_agent = ''

    if request:
        if not actor and hasattr(request, 'user') and request.user.is_authenticated:
            actor = request.user
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        before_state=before_state or {},
        after_state=after_state or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
