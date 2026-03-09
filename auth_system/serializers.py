"""
Сериализаторы для API аутентификации.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Resource, Action, Permission, Role, RolePermission, UserRole

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация: имя, фамилия, отчество, email, пароль, повтор пароля."""
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'patronymic', 'password', 'password_confirm')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Профиль пользователя для просмотра и обновления."""
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'patronymic', 'roles', 'date_joined')
        read_only_fields = ('email', 'date_joined')

    def get_roles(self, obj):
        return [ur.role.name for ur in obj.user_roles.select_related('role').all()]


class LoginSerializer(serializers.Serializer):
    """Вход: email и пароль."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    """Ответ с токенами."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserProfileSerializer()


# Admin API serializers
class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ('id', 'name', 'description')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('id', 'name', 'description')


class PermissionSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    action_name = serializers.CharField(source='action.name', read_only=True)

    class Meta:
        model = Permission
        fields = ('id', 'resource', 'action', 'resource_name', 'action_name')


class RoleSerializer(serializers.ModelSerializer):
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permission_ids', 'permissions')

    def get_permissions(self, obj):
        perms = Permission.objects.filter(role_permissions__role=obj).distinct()
        return PermissionSerializer(perms, many=True).data

    def create(self, validated_data):
        perm_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        for pid in perm_ids:
            RolePermission.objects.get_or_create(
                role=role,
                permission_id=pid
            )
        return role

    def update(self, instance, validated_data):
        perm_ids = validated_data.pop('permission_ids', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if perm_ids is not None:
            instance.role_permissions.exclude(permission_id__in=perm_ids).delete()
            for pid in perm_ids:
                RolePermission.objects.get_or_create(role=instance, permission_id=pid)
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserRole
        fields = ('id', 'user', 'role', 'role_name')


class UserRoleAssignSerializer(serializers.Serializer):
    """Назначение роли пользователю."""
    user_id = serializers.IntegerField()
    role_id = serializers.IntegerField()
