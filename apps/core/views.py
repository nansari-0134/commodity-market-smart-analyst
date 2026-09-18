"""
Core views including health check and system status diagnostics.
"""
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


def health_check(request):
    """
    Lightweight health check endpoint for container orchestrators, load balancers,
    and monitoring agents.
    """
    db_status = "healthy"
    db_vendor = connection.vendor
    try:
        connection.ensure_connection()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    is_healthy = db_status == "healthy"
    payload = {
        "status": "ok" if is_healthy else "degraded",
        "app_name": getattr(settings, "APP_NAME", "Commodity Market Intelligence"),
        "version": getattr(settings, "APP_VERSION", "0.1.0-alpha"),
        "timestamp_utc": timezone.now().isoformat(),
        "database": {
            "status": db_status,
            "vendor": db_vendor,
        },
    }
    return JsonResponse(payload, status=200 if is_healthy else 503)


class SystemStatusAPIView(APIView):
    """
    Detailed REST API status view reporting database, cache, and architectural readiness.
    """

    def get(self, request):
        db_healthy = True
        db_vendor = connection.vendor
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
        except Exception as err:
            db_healthy = False
            db_error = str(err)
        else:
            db_error = None

        data = {
            "status": "online" if db_healthy else "degraded",
            "app_name": getattr(settings, "APP_NAME", "Commodity Intelligence Platform"),
            "version": getattr(settings, "APP_VERSION", "0.1.0-alpha"),
            "timestamp_utc": timezone.now().isoformat(),
            "timezone": settings.TIME_ZONE,
            "phase": "Phase 1: Django + PostgreSQL foundation",
            "database": {
                "connected": db_healthy,
                "vendor": db_vendor,
                "error": db_error,
            },
            "point_in_time_ready": True,
        }
        status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(data, status=status_code)
