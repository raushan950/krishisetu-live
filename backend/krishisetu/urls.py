"""
URL configuration for krishisetu project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok'})
    except Exception:
        return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health_check, name='health_check'),
    path('api/v1/', include('apps.accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
