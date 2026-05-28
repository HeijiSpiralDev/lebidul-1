"""
Django settings for lebidul project - Base configuration.
"""

import os

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = True
ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    # Local apps (before wagtail for template override)
    "apps.agenda",
    "apps.content",
    "apps.theme",
    "apps.migration",

    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",

    # Third party
    "modelcluster",
    "taggit",
    "rest_framework",
    "django_filters",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "lebidul.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
                "apps.theme.context_processors.theme_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "lebidul.wsgi.application"

# Database - SQLite pour le développement local
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Wagtail settings
WAGTAIL_SITE_NAME = "Le Bidul"
WAGTAILADMIN_BASE_URL = os.getenv("WAGTAILADMIN_BASE_URL", "http://localhost:8000")

# Branding
WAGTAIL_ADMIN_LOGO = "images/logo-bidul-admin.png"

WAGTAIL_I18N_ENABLED = False

# Search
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Limites d'upload
WAGTAILIMAGES_IMAGE_MODEL = "wagtailimages.Image"
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB pour les images
WAGTAILDOCS_MAX_UPLOAD_SIZE = 50 * 1024 * 1024    # 50 MB pour les documents (PDFs)

# Limite Django globale
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024    # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024    # 50 MB

# Types de fichiers autorisés pour les documents
WAGTAILDOCS_EXTENSIONS = [
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "rtf", "csv", "zip"
]

# Tailles prédéfinies pour les images
WAGTAILIMAGES_RENDITION_FILTERS = {
    "thumbnail": "fill-100x100",
    "small": "fill-300x300",
    "medium": "fill-600x400",
    "large": "fill-1200x800",
    "hero": "fill-1920x600",
}

# Format par défaut
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    "bmp": "jpeg",
    "webp": "webp",
}

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# Taggit
TAGGIT_CASE_INSENSITIVE = True