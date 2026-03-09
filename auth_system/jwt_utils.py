"""
Собственная реализация JWT — без использования встроенных возможностей фреймворков.
Генерация, валидация и декодирование JWT-токенов.
"""
import jwt
import time
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

JWT_SECRET = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = getattr(settings, 'JWT_ALGORITHM', 'HS256')
ACCESS_LIFETIME = getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', 3600)
REFRESH_LIFETIME = getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', 604800)


def create_access_token(user):
    """Создание access токена для пользователя."""
    now = int(time.time())
    payload = {
        'user_id': user.id,
        'email': user.email,
        'iat': now,
        'exp': now + ACCESS_LIFETIME,
        'type': 'access',
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user):
    """Создание refresh токена для пользователя."""
    now = int(time.time())
    payload = {
        'user_id': user.id,
        'iat': now,
        'exp': now + REFRESH_LIFETIME,
        'type': 'refresh',
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    """
    Декодирование и валидация JWT токена.
    Возвращает payload или None при ошибке.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_access_token(token):
    """
    Получение пользователя из access токена.
    Проверяет last_logout_at для инвалидации токена при logout.
    """
    payload = decode_token(token)
    if not payload or payload.get('type') != 'access':
        return None

    user_id = payload.get('user_id')
    token_iat = payload.get('iat', 0)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

    if not user.is_active:
        return None

    last_logout = getattr(user, 'last_logout_at', None)
    if last_logout and token_iat < last_logout.timestamp():
        return None

    return user
