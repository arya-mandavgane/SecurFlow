"""
Role-based access control (RBAC) permissions for SecurFlow.
"""
from rest_framework import permissions
from .models import User

class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to users with the ADMIN role or superusers.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.role == User.Role.ADMIN or request.user.is_superuser)
        )


class IsOfficialUserRole(permissions.BasePermission):
    """
    Allows access to AICTE Officials and Administrators.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.role in (User.Role.OFFICIAL, User.Role.ADMIN) or request.user.is_superuser)
        )


class IsInstitutionUserRole(permissions.BasePermission):
    """
    Allows access to authorized Institution representatives.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.role == User.Role.INSTITUTION and
            request.user.institution is not None
        )


class IsOwnerInstitutionOrOfficial(permissions.BasePermission):
    """
    Object-level permission:
    - Officials and Admins have global visibility.
    - Institution users can only view or manage records belonging to their own institution.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Admin and Official users can view any institution's records
        if request.user.role in (User.Role.OFFICIAL, User.Role.ADMIN) or request.user.is_superuser:
            return True

        # Institution users must match the institution of the object
        if request.user.role == User.Role.INSTITUTION and request.user.institution:
            # If object is an Institution
            if hasattr(obj, 'aicte_id') and hasattr(obj, 'name'):
                return obj.id == request.user.institution_id

            # If object is an FDR
            if hasattr(obj, 'institution_id'):
                return obj.institution_id == request.user.institution_id

            # If object is an FDRDocument or VerificationRecord
            if hasattr(obj, 'fdr'):
                return obj.fdr.institution_id == request.user.institution_id

            # If object is a ReleaseRequest
            if hasattr(obj, 'fdr'):
                return obj.fdr.institution_id == request.user.institution_id

        return False


class CanVerifyFDR(permissions.BasePermission):
    """
    Only AICTE Officials and Administrators can perform verification actions
    (Approve, Reject, Request Clarification).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.role in (User.Role.OFFICIAL, User.Role.ADMIN) or request.user.is_superuser)
        )
