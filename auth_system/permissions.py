"""
Система проверки прав доступа на основе RBAC.
"""
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed


class IsAuthenticated401(permissions.BasePermission):
    """
    Требует аутентификации. При отсутствии пользователя возвращает 401 (не 403).
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        raise AuthenticationFailed('Требуется аутентификация')


class HasResourcePermission(permissions.BasePermission):
    """
    Проверяет, имеет ли пользователь разрешение на действие над ресурсом.
    Использование: permission_classes = [HasResourcePermission]
    Требует в view: resource_name и action_name (или get_resource_name, get_action_name).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        resource = getattr(view, 'resource_name', None) or getattr(view, 'get_resource_name', lambda: None)()
        action = getattr(view, 'action_name', None) or getattr(view, 'get_action_name', lambda: None)()

        if not resource or not action:
            return False

        return request.user.has_permission(resource, action)


def check_permission(user, resource_name, action_name):
    """
    Проверка: имеет ли пользователь разрешение resource:action.
    """
    if not user or not user.is_authenticated:
        return False
    return user.has_permission(resource_name, action_name)
