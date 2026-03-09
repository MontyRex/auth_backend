"""
URL configuration for auth_backend project.
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include


def home(request):
    """Главная страница — ссылки на API и админку."""
    html = """
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Auth Backend</title></head>
    <body style="font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem;">
        <h1>Auth Backend</h1>
        <p>API аутентификации и авторизации (JWT, RBAC).</p>
        <ul>
            <li><a href="/admin/">Админ-панель</a></li>
            <li><a href="/api/auth/">API аутентификации</a> (регистрация, вход, профиль)</li>
            <li><a href="/api/">API документов, отчётов, настроек</a></li>
        </ul>
    </body>
    </html>
    """
    return HttpResponse(html)


urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_system.urls')),
    path('api/', include('business_app.urls')),
]
