from .base import *
import os

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {"default": dj_database_url.config(env="DATABASE_URL", conn_max_age=600)}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin
]

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
