# Backend: Система аутентификации и авторизации

Собственная реализация аутентификации (JWT) и авторизации (RBAC) без использования встроенных возможностей фреймворков «из коробки».

## Технологии

- Python 3.10+
- Django 4.2
- Django REST Framework
- PostgreSQL (или SQLite для разработки)
- JWT (PyJWT) — собственная реализация без djangorestframework-simplejwt

## Установка

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### База данных

**PostgreSQL** (рекомендуется):

```bash
# Создать БД
createdb auth_backend_db

# Переменные окружения (опционально)
set DB_NAME=auth_backend_db
set DB_USER=postgres
set DB_PASSWORD=postgres
set DB_HOST=localhost
set DB_PORT=5432
```

**SQLite** (для быстрого запуска):

```bash
set USE_POSTGRES=false
```

### Миграции и тестовые данные

```bash
python manage.py migrate
python manage.py seed_rbac
```

### Запуск

```bash
python manage.py runserver
```

## Схема разграничения прав доступа (RBAC)

### Описание структуры

Используется модель **Role-Based Access Control (RBAC)**:

1. **Resource (Ресурс)** — объект системы, к которому применяются правила (например: `documents`, `reports`, `settings`).

2. **Action (Действие)** — операция над ресурсом: `read`, `create`, `update`, `delete`.

3. **Permission (Разрешение)** — связка Resource + Action. Например: `documents:read` — право читать документы.

4. **Role (Роль)** — набор разрешений. Примеры: `admin`, `user`, `manager`.

5. **RolePermission** — связь роли с разрешениями (M:N).

6. **UserRole** — связь пользователя с ролями (M:N). Пользователь может иметь несколько ролей.

### Схема БД (ER-диаграмма)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │     │   UserRole  │     │   Role      │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id          │────<│ user_id     │     │ id          │
│ email       │     │ role_id     │>────│ name        │
│ first_name  │     └─────────────┘     │ description │
│ last_name   │                         └──────┬──────┘
│ patronymic  │                                │
│ is_active   │     ┌─────────────────┐        │
│ ...         │     │ RolePermission   │<───────┘
└─────────────┘     ├─────────────────┤
                    │ role_id         │
                    │ permission_id   │>────┐
                    └─────────────────┘    │
                                           │
┌─────────────┐     ┌─────────────┐       │
│  Resource   │     │ Permission   │<──────┘
├─────────────┤     ├─────────────┤
│ id          │<────│ resource_id │
│ name        │     │ action_id   │>────┐
│ description │     └─────────────┘     │
└─────────────┘                         │
                    ┌─────────────┐      │
                    │   Action    │<────┘
                    ├─────────────┤
                    │ id          │
                    │ name        │
                    │ description │
                    └─────────────┘
```

### Правила доступа

| Роль    | documents | reports | settings |
|---------|-----------|---------|----------|
| admin   | read, create, update, delete | read, create, update, delete | read, update |
| user    | read      | read    | read     |
| manager | read, create | read  | read, update |

### Коды ответов

- **401 Unauthorized** — не удалось определить залогиненного пользователя (нет/неверный токен).
- **403 Forbidden** — пользователь определён, но запрашиваемый ресурс ему недоступен.

## API

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Вход |
| POST | `/api/auth/logout/` | Выход |
| POST | `/api/auth/refresh/` | Обновление access токена |
| GET/PATCH | `/api/auth/profile/` | Профиль |
| POST | `/api/auth/delete-account/` | Мягкое удаление аккаунта |

### Заголовок авторизации

```
Authorization: Bearer <access_token>
```

### Бизнес-объекты (Mock)

| Метод | Endpoint | Разрешение |
|-------|----------|------------|
| GET | `/api/documents/` | documents:read |
| POST | `/api/documents/create/` | documents:create |
| GET | `/api/reports/` | reports:read |
| GET | `/api/reports/<id>/` | reports:read |
| GET | `/api/settings/` | settings:read |
| PUT | `/api/settings/` | settings:update |

### Admin API (только для роли admin)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET/POST | `/api/auth/admin/resources/` | Ресурсы |
| GET/PUT/PATCH/DELETE | `/api/auth/admin/resources/<id>/` | Ресурс |
| GET/POST | `/api/auth/admin/actions/` | Действия |
| GET/POST | `/api/auth/admin/permissions/` | Разрешения |
| GET/POST | `/api/auth/admin/roles/` | Роли |
| POST | `/api/auth/admin/assign-role/` | Назначить роль |
| DELETE | `/api/auth/admin/revoke-role/<user_id>/<role_id>/` | Снять роль |

## Тестовые пользователи (после seed_rbac)

| Email | Пароль | Роль |
|-------|--------|------|
| admin@example.com | admin123 | admin |
| user@example.com | user123 | user |
| manager@example.com | manager123 | manager |

## Примеры запросов

### Регистрация

```json
POST /api/auth/register/
{
  "email": "test@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "patronymic": "Иванович",
  "password": "securepass123",
  "password_confirm": "securepass123"
}
```

### Вход

```json
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "user123"
}
```

Ответ: `access_token`, `refresh_token`, `user`.

### Запрос к защищённому ресурсу

```
GET /api/documents/
Authorization: Bearer <access_token>
```

## JWT

- **Access token** — короткоживущий (1 час), передаётся в заголовке.
- **Refresh token** — долгоживущий (7 дней), используется для обновления access.
- **Logout** — при выходе устанавливается `last_logout_at`; все токены, выданные до этого момента, становятся недействительными.

## Мягкое удаление

При вызове `POST /api/auth/delete-account/` пользователь деактивируется (`is_active=False`), выполняется логика logout. Данные в БД сохраняются, вход становится невозможен.

---

