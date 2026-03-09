"""
Заполнение БД тестовыми данными RBAC и пользователями.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from auth_system.models import Resource, Action, Permission, Role, RolePermission, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт тестовые ресурсы, действия, разрешения, роли и пользователей'

    def handle(self, *args, **options):
        self.stdout.write('Создание ресурсов...')
        resources = {}
        for name, desc in [
            ('documents', 'Документы'),
            ('reports', 'Отчёты'),
            ('settings', 'Настройки'),
        ]:
            r, _ = Resource.objects.get_or_create(name=name, defaults={'description': desc})
            resources[name] = r

        self.stdout.write('Создание действий...')
        actions = {}
        for name, desc in [
            ('read', 'Чтение'),
            ('create', 'Создание'),
            ('update', 'Обновление'),
            ('delete', 'Удаление'),
        ]:
            a, _ = Action.objects.get_or_create(name=name, defaults={'description': desc})
            actions[name] = a

        self.stdout.write('Создание разрешений...')
        perms = {}
        perm_list = [
            ('documents', 'read'), ('documents', 'create'), ('documents', 'update'), ('documents', 'delete'),
            ('reports', 'read'), ('reports', 'create'), ('reports', 'update'), ('reports', 'delete'),
            ('settings', 'read'), ('settings', 'update'),
        ]
        for res_name, act_name in perm_list:
            key = f'{res_name}:{act_name}'
            p, _ = Permission.objects.get_or_create(
                resource=resources[res_name],
                action=actions[act_name]
            )
            perms[key] = p

        self.stdout.write('Создание ролей...')
        admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'description': 'Администратор'})
        user_role, _ = Role.objects.get_or_create(name='user', defaults={'description': 'Обычный пользователь'})
        manager_role, _ = Role.objects.get_or_create(name='manager', defaults={'description': 'Менеджер'})

        for p in perms.values():
            RolePermission.objects.get_or_create(role=admin_role, permission=p)

        for key in ['documents:read', 'reports:read', 'settings:read']:
            RolePermission.objects.get_or_create(role=user_role, permission=perms[key])

        for key in ['documents:read', 'documents:create', 'reports:read', 'settings:read', 'settings:update']:
            RolePermission.objects.get_or_create(role=manager_role, permission=perms[key])

        self.stdout.write('Создание тестовых пользователей...')
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Админ',
                'last_name': 'Системы',
                'patronymic': 'Иванович',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        else:
            # чтобы существующий админ мог входить в /admin/
            if not admin_user.is_staff or not admin_user.is_superuser:
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save(update_fields=['is_staff', 'is_superuser'])
        UserRole.objects.get_or_create(user=admin_user, role=admin_role)

        user1, created = User.objects.get_or_create(
            email='user@example.com',
            defaults={
                'first_name': 'Петр',
                'last_name': 'Петров',
                'patronymic': 'Петрович',
                'is_active': True,
            }
        )
        if created:
            user1.set_password('user123')
            user1.save()
        UserRole.objects.get_or_create(user=user1, role=user_role)

        manager1, created = User.objects.get_or_create(
            email='manager@example.com',
            defaults={
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'patronymic': 'Александровна',
                'is_active': True,
            }
        )
        if created:
            manager1.set_password('manager123')
            manager1.save()
        UserRole.objects.get_or_create(user=manager1, role=manager_role)

        self.stdout.write(self.style.SUCCESS('Готово! Тестовые пользователи:'))
        self.stdout.write('  admin@example.com / admin123 (роль: admin)')
        self.stdout.write('  user@example.com / user123 (роль: user)')
        self.stdout.write('  manager@example.com / manager123 (роль: manager)')
