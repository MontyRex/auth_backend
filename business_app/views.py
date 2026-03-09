"""
Mock-представления бизнес-объектов:
документы, отчёты, настройки.
Проверка доступа по RBAC (resource:action).
"""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_system.permissions import IsAuthenticated401


def check_permission_and_response(request, resource_name, action_name):
    """
    Проверяет право доступа. Возвращает (user, None) при успехе или (None, Response) при ошибке.
    """
    if not request.user or not request.user.is_authenticated:
        return None, Response(
            {'detail': 'Требуется аутентификация'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not request.user.has_permission(resource_name, action_name):
        return None, Response(
            {'detail': 'Доступ запрещён'},
            status=status.HTTP_403_FORBIDDEN
        )
    return request.user, None


# Mock данные
MOCK_DOCUMENTS = [
    {'id': 1, 'title': 'Договор поставки №1', 'client': 'ООО Ромашка'},
    {'id': 2, 'title': 'Акт выполненных работ', 'client': 'ИП Иванов'},
    {'id': 3, 'title': 'Счёт на оплату', 'client': 'ЗАО Вектор'},
]

MOCK_REPORTS = [
    {'id': 1, 'name': 'Отчёт по продажам за январь', 'period': '2025-01'},
    {'id': 2, 'name': 'Отчёт по продажам за февраль', 'period': '2025-02'},
]


@api_view(['GET'])
@permission_classes([IsAuthenticated401])
def document_list(request):
    """Список документов: требуется documents:read."""
    user, err = check_permission_and_response(request, 'documents', 'read')
    if err:
        return err
    return Response({'documents': MOCK_DOCUMENTS})


@api_view(['POST'])
@permission_classes([IsAuthenticated401])
def document_create(request):
    """Создание документа: требуется documents:create."""
    user, err = check_permission_and_response(request, 'documents', 'create')
    if err:
        return err
    return Response({
        'id': 99,
        'title': request.data.get('title', 'Новый документ'),
        'client': request.data.get('client', ''),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated401])
def report_list(request):
    """Список отчётов: требуется reports:read."""
    user, err = check_permission_and_response(request, 'reports', 'read')
    if err:
        return err
    return Response({'reports': MOCK_REPORTS})


@api_view(['GET'])
@permission_classes([IsAuthenticated401])
def report_detail(request, pk):
    """Детали отчёта: требуется reports:read."""
    user, err = check_permission_and_response(request, 'reports', 'read')
    if err:
        return err
    for r in MOCK_REPORTS:
        if r['id'] == int(pk):
            return Response(r)
    return Response({'detail': 'Не найдено'}, status=404)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated401])
def settings_view(request):
    """Настройки системы: требуется settings:read для GET, settings:update для PUT."""
    if request.method == 'GET':
        user, err = check_permission_and_response(request, 'settings', 'read')
    else:
        user, err = check_permission_and_response(request, 'settings', 'update')
    if err:
        return err
    if request.method == 'GET':
        return Response({
            'theme': 'light',
            'language': 'ru',
            'notifications': True,
        })
    return Response({
        'theme': request.data.get('theme', 'light'),
        'language': request.data.get('language', 'ru'),
        'notifications': request.data.get('notifications', True),
    })


def business_api_index(request):
    """Страница со списком эндпоинтов бизнес-API."""
    base = request.build_absolute_uri('/').rstrip('/')
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>API документов, отчётов, настроек</title></head>
    <body style="font-family: sans-serif; max-width: 560px; margin: 2rem auto; padding: 0 1rem;">
        <h1>API документов, отчётов и настроек</h1>
        <p>Эндпоинты требуют авторизации (Bearer token).</p>
        <ul>
            <li><a href="{base}/api/documents/">GET /api/documents/</a> — список документов (documents:read)</li>
            <li><a href="{base}/api/documents/create/">POST /api/documents/create/</a> — создать документ (documents:create)</li>
            <li><a href="{base}/api/reports/">GET /api/reports/</a> — список отчётов (reports:read)</li>
            <li><a href="{base}/api/reports/1/">GET /api/reports/&lt;id&gt;/</a> — отчёт по id</li>
            <li><a href="{base}/api/settings/">GET/PUT /api/settings/</a> — настройки (settings:read/update)</li>
        </ul>
        <p><a href="{base}/">← На главную</a></p>
    </body></html>
    """
    return HttpResponse(html)
