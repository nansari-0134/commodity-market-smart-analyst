"""
URL Configuration for Commodity Market Intelligence System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Core health checks and system status
    path("", include("apps.core.urls")),
    # Metadata catalog APIs
    path("api/metadata/", include("apps.metadata.urls")),
    # Main terminal / intelligence dashboard
    path("", include("apps.dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
