"""
Celery configuration for Commodity Market Intelligence System.
"""
import os
from celery import Celery

# Set default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("commodity_intelligence")

# Load configuration from Django settings with namespace 'CELERY'
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Diagnostic task for verifying Celery worker health."""
    print(f"Request: {self.request!r}")
