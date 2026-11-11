from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('institutions/', include('institutions.urls')),
    path('academics/', include('academics.urls')),
    path('resources/', include('resources.urls')),
    path('teaching/', include('teaching.urls')),
    path('examinations/', include('examinations.urls')),
    path('notifications/', include('notifications.urls')),
    path('audit/', include('audit.urls')),
    path('conflicts/', include('conflicts.urls')),
    path('imports/', include('imports_exports.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('reports/', include('reports.urls')),
    path('', include('public.urls')),
    path('', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
