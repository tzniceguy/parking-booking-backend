from rest_framework import permissions

class IsOperatorOrReadOnly(permissions.BasePermission):
    """custom permission to allow only operators of an object to edit or delete it
        Read only access is allowed to any user
    """
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.operator == request.user