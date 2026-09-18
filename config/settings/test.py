"""
Test settings for Commodity Market Intelligence System.
Optimized for rapid test execution.
"""
from .base import *  # noqa: F403

DEBUG = False
TESTING = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
