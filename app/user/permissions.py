from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to superusers.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsStaffOrSuperUser(permissions.BasePermission):
    """
    Allows access only to staff or superusers.
    """

    def has_permission(self, request, view):
        return request.user and (request.user.is_staff
                                 or request.user.is_superuser)
