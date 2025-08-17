from rest_framework import permissions


class RoleBasedPermission(permissions.BasePermission):
    """
    Custom permission class for role-based access control
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        
        # Admin has full access
        if user.is_admin:
            return True
            
        # Staff can perform CRUD operations
        if user.is_staff_member and request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            return True
            
        # Viewer has read-only access
        if user.role == 'viewer' and request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
            
        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        
        # Admin has full access to all objects
        if user.is_admin:
            return True
            
        # Staff can modify objects
        if user.is_staff_member:
            return True
            
        # Viewer can only read
        if user.role == 'viewer' and request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
            
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission for user management - only admins can create/modify users
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for admin users
        return request.user.is_admin


class StockLogPermission(permissions.BasePermission):
    """
    Stock logs are read-only for audit purposes
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Only read access allowed
        return request.method in permissions.SAFE_METHODS