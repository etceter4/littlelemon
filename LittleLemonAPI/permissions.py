from rest_framework import permissions

class IsManager(permissions.BasePermission):

    def has_permission(self, request, view):
        # Check if the user belongs to Manager group or is an admin (is_staff or is_superuser)
        return request.user.groups.filter(name='Manager').exists() or request.user.is_staff or request.user.is_superuser
    

class IsDeliveryCrew(permissions.BasePermission):
    """
    Custom permission to only allow members of the delivery crew to access the order.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name='Delivery Crew').exists()
