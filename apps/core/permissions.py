from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission: only allow access if obj.user == request.user.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsPremiumUser(BasePermission):
    """
    Allows access only to premium subscribers.
    """
    message = 'This feature requires a premium subscription.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_premium)
