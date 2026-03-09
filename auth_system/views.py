"""
API views для аутентификации и управления пользователями.
"""
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .permissions import IsAuthenticated401
from rest_framework.response import Response

from .models import User, Resource, Action, Permission, Role, RolePermission, UserRole
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    LoginSerializer,
    TokenResponseSerializer,
    ResourceSerializer,
    ActionSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserRoleSerializer,
    UserRoleAssignSerializer,
)
from .jwt_utils import create_access_token, create_refresh_token, decode_token, get_user_from_access_token


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Регистрация пользователя."""
    serializer = UserRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    access = create_access_token(user)
    refresh = create_refresh_token(user)
    return Response({
        'access_token': access,
        'refresh_token': refresh,
        'user': UserProfileSerializer(user).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Вход по email и паролю."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'detail': 'Неверный email или пароль'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'detail': 'Учётная запись деактивирована'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.check_password(password):
        return Response(
            {'detail': 'Неверный email или пароль'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    access = create_access_token(user)
    refresh = create_refresh_token(user)
    return Response({
        'access_token': access,
        'refresh_token': refresh,
        'user': UserProfileSerializer(user).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated401])
def logout(request):
    """Выход из системы — инвалидация токенов через last_logout_at."""
    user = request.user
    user.last_logout_at = timezone.now()
    user.save(update_fields=['last_logout_at'])
    return Response({'detail': 'Вы успешно вышли из системы'})


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Обновление access токена по refresh токену."""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Требуется refresh токен'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    token = auth_header[7:].strip()
    payload = decode_token(token)
    if not payload or payload.get('type') != 'refresh':
        return Response(
            {'detail': 'Недействительный или истёкший refresh токен'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    try:
        user = User.objects.get(id=payload['user_id'])
    except User.DoesNotExist:
        return Response(
            {'detail': 'Пользователь не найден'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not user.is_active:
        return Response(
            {'detail': 'Учётная запись деактивирована'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    access = create_access_token(user)
    return Response({'access_token': access})


class ProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и обновление профиля текущего пользователя."""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated401]

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated401])
def delete_account(request):
    """Мягкое удаление аккаунта: is_active=False, logout."""
    user = request.user
    user.is_active = False
    user.last_logout_at = timezone.now()
    user.save(update_fields=['is_active', 'last_logout_at'])
    return Response({'detail': 'Аккаунт успешно удалён'})


def admin_required(view_func):
    """Декоратор: только пользователь с ролью admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Требуется аутентификация'}, status=401)
        if not request.user.has_admin_role():
            return Response({'detail': 'Доступ запрещён'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# Admin API views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated401])
def resource_list_create(request):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    if request.method == 'GET':
        qs = Resource.objects.all()
        return Response(ResourceSerializer(qs, many=True).data)
    serializer = ResourceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=201)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated401])
def resource_detail(request, pk):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    try:
        obj = Resource.objects.get(pk=pk)
    except Resource.DoesNotExist:
        return Response(status=404)
    if request.method == 'GET':
        return Response(ResourceSerializer(obj).data)
    if request.method in ('PUT', 'PATCH'):
        serializer = ResourceSerializer(obj, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    obj.delete()
    return Response(status=204)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated401])
def action_list_create(request):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    if request.method == 'GET':
        return Response(ActionSerializer(Action.objects.all(), many=True).data)
    serializer = ActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=201)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated401])
def action_detail(request, pk):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    try:
        obj = Action.objects.get(pk=pk)
    except Action.DoesNotExist:
        return Response(status=404)
    if request.method == 'GET':
        return Response(ActionSerializer(obj).data)
    if request.method in ('PUT', 'PATCH'):
        serializer = ActionSerializer(obj, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    obj.delete()
    return Response(status=204)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated401])
def permission_list_create(request):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    if request.method == 'GET':
        qs = Permission.objects.select_related('resource', 'action').all()
        return Response(PermissionSerializer(qs, many=True).data)
    serializer = PermissionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=201)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated401])
def permission_detail(request, pk):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    try:
        obj = Permission.objects.get(pk=pk)
    except Permission.DoesNotExist:
        return Response(status=404)
    if request.method == 'GET':
        return Response(PermissionSerializer(obj).data)
    if request.method in ('PUT', 'PATCH'):
        serializer = PermissionSerializer(obj, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    obj.delete()
    return Response(status=204)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated401])
def role_list_create(request):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    if request.method == 'GET':
        qs = Role.objects.prefetch_related('role_permissions__permission__resource', 'role_permissions__permission__action')
        return Response(RoleSerializer(qs, many=True).data)
    serializer = RoleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=201)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated401])
def role_detail(request, pk):
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    try:
        obj = Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        return Response(status=404)
    if request.method == 'GET':
        return Response(RoleSerializer(obj).data)
    if request.method in ('PUT', 'PATCH'):
        serializer = RoleSerializer(obj, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    obj.delete()
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated401])
def assign_role(request):
    """Назначить роль пользователю."""
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    serializer = UserRoleAssignSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    ur, created = UserRole.objects.get_or_create(
        user_id=serializer.validated_data['user_id'],
        role_id=serializer.validated_data['role_id']
    )
    return Response(UserRoleSerializer(ur).data, status=201 if created else 200)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated401])
def revoke_role(request, user_id, role_id):
    """Снять роль с пользователя."""
    if not request.user.has_admin_role():
        return Response({'detail': 'Доступ запрещён'}, status=403)
    deleted, _ = UserRole.objects.filter(user_id=user_id, role_id=role_id).delete()
    if not deleted:
        return Response(status=404)
    return Response(status=204)


def auth_api_index(request):
    """Страница со списком эндпоинтов API аутентификации."""
    base = request.build_absolute_uri('/').rstrip('/')
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>API аутентификации</title></head>
    <body style="font-family: sans-serif; max-width: 560px; margin: 2rem auto; padding: 0 1rem;">
        <h1>API аутентификации</h1>
        <p>Регистрация, вход, JWT, профиль, RBAC.</p>
        <ul>
            <li><a href="{base}/api/auth/register/">POST /api/auth/register/</a> — регистрация</li>
            <li><a href="{base}/api/auth/login/">POST /api/auth/login/</a> — вход</li>
            <li><a href="{base}/api/auth/logout/">POST /api/auth/logout/</a> — выход</li>
            <li><a href="{base}/api/auth/refresh/">POST /api/auth/refresh/</a> — обновление токена</li>
            <li><a href="{base}/api/auth/profile/">GET/PATCH /api/auth/profile/</a> — профиль</li>
            <li><a href="{base}/api/auth/delete-account/">POST /api/auth/delete-account/</a> — удаление аккаунта</li>
            <li><a href="{base}/api/auth/admin/resources/">Admin: ресурсы</a></li>
            <li><a href="{base}/api/auth/admin/roles/">Admin: роли</a></li>
        </ul>
        <p><a href="{base}/">← На главную</a></p>
    </body></html>
    """
    return HttpResponse(html)
