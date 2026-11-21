from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Faqat role='admin' bo'lgan foydalanuvchilarga ruxsat beradi."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == "admin" or request.user.is_superuser or request.user.is_staff)
        )


class IsAdminOrReadOnly(BasePermission):
    """GET, HEAD, OPTIONS — hammaga; yozish/tahrirlash — faqat adminga."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == "admin" or request.user.is_superuser or request.user.is_staff)
        )
