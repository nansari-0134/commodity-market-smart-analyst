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

# Ensure tests always use offline deterministic static providers
MARKET_DATA_PROVIDER = "static"
FUNDAMENTAL_DATA_PROVIDER = "static"
COT_DATA_PROVIDER = "static"
NEWS_PROVIDER = "static"
LLM_PROVIDER = "static"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
