from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv

# ============================================================
# BASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# SECRET KEY
# ============================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-development-only-change-this-key",
)


# ============================================================
# DEBUG
# ============================================================

DEBUG = (
    os.environ.get(
        "DJANGO_DEBUG",
        "True",
    ).lower()
    == "true"
)


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


# ============================================================
# HTTPS / SECURITY SETTINGS
# ============================================================

SECURE_SSL_REDIRECT = (
    os.environ.get(
        "SECURE_SSL_REDIRECT",
        "False",
    ).lower()
    == "true"
)

SESSION_COOKIE_SECURE = (
    os.environ.get(
        "SESSION_COOKIE_SECURE",
        "False",
    ).lower()
    == "true"
)

CSRF_COOKIE_SECURE = (
    os.environ.get(
        "CSRF_COOKIE_SECURE",
        "False",
    ).lower()
    == "true"
)

SECURE_HSTS_SECONDS = int(
    os.environ.get(
        "SECURE_HSTS_SECONDS",
        "0",
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.environ.get(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        "False",
    ).lower()
    == "true"
)

SECURE_HSTS_PRELOAD = (
    os.environ.get(
        "SECURE_HSTS_PRELOAD",
        "False",
    ).lower()
    == "true"
)

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = os.environ.get(
    "SECURE_REFERRER_POLICY",
    "same-origin",
)


# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "users",
    "patients",
    "doctors",
    "medical_records",
    "access_control",
    "consultations",
    "appointments",
    "prescriptions",
    "chat",
    "notifications",
    "documents",
    "consents",
    "audit_logs",
    "rest_framework_simplejwt.token_blacklist",
    "emergency_card",
    "security",
    "admin_portal",
    "blockchain",
    "payments",
]


# ============================================================
# CORS
# ============================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "config.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {"NAME": ("django.contrib.auth.password_validation." "MinimumLengthValidator")},
    {"NAME": ("django.contrib.auth.password_validation." "CommonPasswordValidator")},
    {"NAME": ("django.contrib.auth.password_validation." "NumericPasswordValidator")},
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "static/"


# ============================================================
# AROVA PUBLIC URL
# ============================================================

AROVA_CARE_PUBLIC_URL = os.environ.get(
    "AROVA_CARE_PUBLIC_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# ============================================================
# SECURITY SESSION TIMEOUT
# ============================================================

SECURITY_SESSION_TIMEOUT_SECONDS = int(
    os.environ.get(
        "SECURITY_SESSION_TIMEOUT_SECONDS",
        "1800",
    )
)


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# CUSTOM USER MODEL
# ============================================================

AUTH_USER_MODEL = "users.User"


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "security.authentication.ArovaJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/minute",
    },
    "EXCEPTION_HANDLER": ("config.exceptions.arova_exception_handler"),
}


# ============================================================
# SIMPLE JWT
# ============================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": ("HTTP_AUTHORIZATION"),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "LEEWAY": 0,
}


# ============================================================
# RAZORPAY
# ============================================================

RAZORPAY_KEY_ID = os.environ.get(
    "RAZORPAY_KEY_ID",
    "",
)

RAZORPAY_KEY_SECRET = os.environ.get(
    "RAZORPAY_KEY_SECRET",
    "",
)

RAZORPAY_WEBHOOK_SECRET = os.environ.get(
    "RAZORPAY_WEBHOOK_SECRET",
    "",
)
