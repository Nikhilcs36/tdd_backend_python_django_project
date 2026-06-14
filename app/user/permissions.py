from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to superusers.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsStaffOrSuperUser(permissions.BasePermission):
    """
    Allows access only to staff or superusers with active_role enabled.

    Respects the active_role field so that when a user switches to
    'regular' role, they are denied access to staff-only endpoints.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # Superuser has access when active_role is 'superuser' or 'staff'
        if user.is_superuser and user.active_role in ('superuser', 'staff'):
            return True
        # Staff user has access only when active_role is 'staff'
        if user.is_staff and user.active_role == 'staff':
            return True
        return False


class UserDetailPermission(permissions.BasePermission):
    """
    Custom permission for UserDetailView with role-based access control.

    Permission matrix:
    - Regular user: Can view and edit their own record only.
    - Staff user: Can view any user's record (read-only), edit own record only.
    - Superuser: Full access (view, edit, delete any record).
    """

    def has_permission(self, request, view):
        """Authenticated users can access the endpoint (object-level
        check handles further restrictions)."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions based on user role."""
        user = request.user

        # Superuser has full access
        if user.is_superuser:
            return True

        # DELETE is only allowed for superusers
        if request.method == 'DELETE':
            return False

        # Staff can view any record (read-only) and edit their own
        if user.is_staff:
            if request.method in permissions.SAFE_METHODS:
                return True  # Staff can view any record
            # Staff can only edit their own record
            return obj == user

        # Regular user can only access their own record
        if request.method in permissions.SAFE_METHODS:
            return obj == user
        # Regular user can edit their own record
        if request.method in ('PUT', 'PATCH'):
            return obj == user

        return False
