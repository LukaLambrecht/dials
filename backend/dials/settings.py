"""
Django settings for dials project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import json
import os.path
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers
from decouple import config


# Discover which environment the server is running
ENV = config("DJANGO_ENV")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(config("DJANGO_DEBUG", cast=int, default=0))  # 0 is False

# A list of strings representing the host/domain names that this Django site can serve
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="").split(" ")

# A list of trusted origins for unsafe requests (e.g. POST).
CSRF_TRUSTED_ORIGINS = config("DJANGO_CSRF_TRUSTED_ORIGINS", default="").split(" ")

# Cors
WORKSPACE_HEADER = "workspace"

CORS_ALLOW_ALL_ORIGINS = False  # If this is True then `CORS_ALLOWED_ORIGINS` will not have any effect

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = config("DJANGO_CORS_ALLOWED_ORIGINS", default="").split(" ")

CORS_ALLOW_HEADERS = [*default_headers, WORKSPACE_HEADER]

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "dqmio_file_indexer.apps.DqmioDataIndexerConfig",
    "dqmio_etl.apps.DqmioEtlConfig",
    "cern_auth.apps.CERNAuthConfig",
]

# Django Rest Framework (DRF) configuration
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "utils.paginate.LargeTablePageNumberPagination",
    "PAGE_SIZE": 10,
}

# A list of middleware (framework of hooks into Django's request/response processing) to use
MIDDLEWARE = [
    "debreach.middleware.RandomCommentMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

# A string representing the full Python import path to your root URLconf
ROOT_URLCONF = "dials.urls"

# A list containing the settings for all template engines to be used with Django
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

# Indicate entrypoint for starting ASGI server
ASGI_APPLICATION = "dials.asgi.application"

# Database configuration
WORKSPACES = json.loads(config("DJANGO_WORKSPACES", default="{}"))
if len(WORKSPACES) == 0:
    raise Exception("Workspaces are empty, cannot start server.")

DB_SERVER_URI = config("DJANGO_DATABASE_URI")
DEFAULT_WORKSPACE = config("DJANGO_DEFAULT_WORKSPACE", default=None)
DEFAULT_WORKSPACE = DEFAULT_WORKSPACE if DEFAULT_WORKSPACE else WORKSPACES.keys()[0]
DATABASES = {name: dj_database_url.config(default=os.path.join(DB_SERVER_URI, name)) for name in WORKSPACES.keys()}
DATABASES["default"] = DATABASES[DEFAULT_WORKSPACE]

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"level": "DEBUG" if DEBUG else "WARNING", "class": "logging.StreamHandler", "formatter": "standard"}
    },
    "formatters": {
        "standard": {
            "format": "{levelname} - {asctime} - {module} - {message}",
            "style": "{",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "WARNING",
            "propagate": False,
        },
        "root": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "WARNING", "propagate": False},
    },
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Keycloak OIDC config
KEYCLOAK_SERVER_URL = config("DJANGO_KEYCLOAK_SERVER_URL")
KEYCLOAK_REALM = config("DJANGO_KEYCLOAK_REALM")
KEYCLOAK_CONFIDENTIAL_CLIENT_ID = config("DJANGO_KEYCLOAK_CONFIDENTIAL_CLIENT_ID")
KEYCLOAK_CONFIDENTIAL_SECRET_KEY = config("DJANGO_KEYCLOAK_CONFIDENTIAL_SECRET_KEY")
KEYCLOAK_PUBLIC_CLIENT_ID = config("DJANGO_KEYCLOAK_PUBLIC_CLIENT_ID")
KEYCLOAK_API_CLIENTS = json.loads(config("DJANGO_KEYCLOAK_API_CLIENTS", default="{}"))

# All available policies are listed at:
# https://github.com/w3c/webappsec-permissions-policy/blob/main/features.md
# Empty list means the policy is disabled
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "camera": [],
    "display-capture": [],
    "encrypted-media": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
    "xr-spatial-tracking": [],
}

# Django-CSP
CSP_INCLUDE_NONCE_IN = ["script-src", "connect-src", "style-src", "font-src", "img-src"]
CSP_SCRIPT_SRC = [
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js",
] + [f"*{host}" if host.startswith(".") else host for host in ALLOWED_HOSTS]
CSP_CONNECT_SRC = [
    "'self'",
] + [f"*{host}" if host.startswith(".") else host for host in ALLOWED_HOSTS]
CSP_STYLE_SRC = [
    "'self'",
    "'unsafe-inline'",
    "https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css",
]
CSP_FONT_SRC = [
    "'self'",
    "'unsafe-inline'",
] + [f"*{host}" if host.startswith(".") else host for host in ALLOWED_HOSTS]
CSP_IMG_SRC = [
    "'self'",
    "data:",
    "https://unpkg.com/swagger-ui-dist@5.11.0/favicon-32x32.png",
]

# # Caching
CACHE_TTL = 60 * 15  # 15 minutes
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("DJANGO_REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "IGNORE_EXCEPTIONS": True,
        },
    }
}
