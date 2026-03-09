"""
Модели системы аутентификации и авторизации.

Схема RBAC (Role-Based Access Control):
- User: пользователь системы
- Role: роль (администратор, менеджер, пользователь и т.д.)
- Resource: ресурс системы (документы, отчёты, настройки и т.д.)
- Action: действие над ресурсом (read, create, update, delete)
- Permission: связка Resource + Action (разрешение на конкретное действие над ресурсом)
- RolePermission: связь роли с разрешениями (какие разрешения имеет роль)
- UserRole: связь пользователя с ролями (какие роли назначены пользователю)
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Менеджер пользователей с email в качестве идентификатора."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Кастомная модель пользователя.
    is_active=False при мягком удалении — пользователь не может войти.
    """
    email = models.EmailField('Email', unique=True)
    first_name = models.CharField('Имя', max_length=150, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    patronymic = models.CharField('Отчество', max_length=150, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    is_staff = models.BooleanField('Персонал', default=False)
    last_logout_at = models.DateTimeField('Время последнего выхода', null=True, blank=True)
    date_joined = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join(p for p in parts if p).strip() or self.email

    def has_permission(self, resource_name, action_name):
        """
        Проверяет, имеет ли пользователь разрешение на action над resource.
        """
        if self.is_superuser:
            return True
        return Permission.objects.filter(
            resource__name=resource_name,
            action__name=action_name
        ).filter(
            role_permissions__role__user_roles__user=self
        ).exists()

    def has_admin_role(self):
        """Проверяет, имеет ли пользователь роль администратора."""
        if self.is_superuser:
            return True
        return self.user_roles.filter(role__name='admin').exists()

    def __str__(self):
        return self.email


class Resource(models.Model):
    """Ресурс системы — объект, к которому применяются правила доступа."""
    name = models.CharField('Код ресурса', max_length=100, unique=True)
    description = models.CharField('Описание', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Ресурс'
        verbose_name_plural = 'Ресурсы'

    def __str__(self):
        return self.name


class Action(models.Model):
    """Действие над ресурсом (read, create, update, delete)."""
    name = models.CharField('Код действия', max_length=50, unique=True)
    description = models.CharField('Описание', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Действие'
        verbose_name_plural = 'Действия'

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Разрешение = Resource + Action (например: documents:read)."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='permissions')
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='permissions')

    class Meta:
        verbose_name = 'Разрешение'
        verbose_name_plural = 'Разрешения'
        unique_together = ['resource', 'action']

    def __str__(self):
        return f'{self.resource.name}:{self.action.name}'


class Role(models.Model):
    """Роль пользователя (admin, manager, user и т.д.)."""
    name = models.CharField('Название', max_length=100, unique=True)
    description = models.CharField('Описание', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """Связь роли с разрешениями."""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')

    class Meta:
        verbose_name = 'Разрешение роли'
        verbose_name_plural = 'Разрешения ролей'
        unique_together = ['role', 'permission']

    def __str__(self):
        return f'{self.role.name} -> {self.permission}'


class UserRole(models.Model):
    """Связь пользователя с ролями."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')

    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
        unique_together = ['user', 'role']

    def __str__(self):
        return f'{self.user.email} -> {self.role.name}'
