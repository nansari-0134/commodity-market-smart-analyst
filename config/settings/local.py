"""
Local development settings for Commodity Market Intelligence System.
"""
from .base import *  # noqa: F403

DEBUG = True

# Allows all local interfaces for convenient development
ALLOWED_HOSTS = ["*"]

# In local dev, if debug toolbar is added later, configure internal IPs
INTERNAL_IPS = ["127.0.0.1"]

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
