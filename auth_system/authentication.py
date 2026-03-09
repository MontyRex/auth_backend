"""
Кастомная JWT аутентификация — не использует встроенные механизмы DRF.
"""
from rest_framework import authentication
from rest_framework import exceptions

from .jwt_utils import get_user_from_access_token


class CustomJWTAuthentication(authentication.BaseAuthentication):
    """
    Аутентификация по JWT в заголовке Authorization: Bearer <token>.
    При неудаче не возвращает пользователя (не 401 здесь — DRF обработает).
    """
    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header or not auth_header.startswith(f'{self.keyword} '):
            return None

        token = auth_header[len(self.keyword) + 1:].strip()
        if not token:
            return None

        user = get_user_from_access_token(token)
        if user is None:
            raise exceptions.AuthenticationFailed('Недействительный или истёкший токен')

        return (user, token)
