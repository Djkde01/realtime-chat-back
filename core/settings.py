"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from dotenv import load_dotenv
from pathlib import Path
import dj_database_url


# Load environment variables
load_dotenv()

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-key-for-development")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("ENVIRONMENT") != "production"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "channels",
    "rest_framework_simplejwt",
    "corsheaders",
    "storages",  # For CDN integration
    "drf_yasg",
    # Local apps
    "authentication",
    "chat",
    "reactions",
    "socket_handlers",
    "core",
]

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Channels settings
ASGI_APPLICATION = "core.asgi.application"
# Channel Layers configuration
if os.environ.get("REDIS_URL"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get("REDIS_URL")],
            },
        },
    }
else:
    # Use in-memory channel layer for development
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Cors settings
CORS_ALLOW_ALL_ORIGINS = False

# Parse CORS origins from environment variable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    # Convert string representation to actual list
    import ast

    try:
        CORS_ALLOWED_ORIGINS = ast.literal_eval(allowed_origins_str)
    except (ValueError, SyntaxError):
        # Fallback if parsing fails
        CORS_ALLOWED_ORIGINS = ["http://localhost:8081", "exp://192.168.1.167:8081"]
else:
    # Default if environment variable is not set
    CORS_ALLOWED_ORIGINS = ["http://localhost:8081", "exp://192.168.1.167:8081"]

# Allow credentials in requests (important for auth)
CORS_ALLOW_CREDENTIALS = True

# Allow specific headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

ROOT_URLCONF = "core.urls"

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

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Database configuration
if os.environ.get("DATABASE_URL"):
    # Parse the DATABASE_URL but we'll add custom options
    db_config = dj_database_url.parse(
        os.environ.get("DATABASE_URL"),
        conn_max_age=600,
    )

    # Add Supabase-specific options
    db_config["OPTIONS"] = {
        "sslmode": "require",  # Supabase requires SSL
        "connect_timeout": 30,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
        "target_session_attrs": "read-write",
    }

    DATABASES = {"default": db_config}
else:
    # Your local database settings remain unchanged
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DATABASE_NAME", "postgres"),
            "USER": os.environ.get("DATABASE_USER", "postgres"),
            "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
            "HOST": os.environ.get("DATABASE_HOST", "localhost"),
            "PORT": os.environ.get("DATABASE_PORT", "5432"),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


DATABASE_ROUTERS = ["core.database_routers.DatabaseRouter"]


AUTH_USER_MODEL = "authentication.User"

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}


# Cloudflare R2 Settings
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_STORAGE_BUCKET_NAME = os.getenv("R2_STORAGE_BUCKET_NAME")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_CUSTOM_DOMAIN = os.getenv("R2_CUSTOM_DOMAIN", f"{R2_ACCOUNT_ID}.r2.dev")

# Media storage configuration
DEFAULT_FILE_STORAGE = "core.storage_backends.MediaStorage"


# Public URL access via Workers
if os.getenv("R2_WORKER_ENABLED", "False").lower() == "true":
    R2_CUSTOM_DOMAIN = os.getenv("R2_WORKER_DOMAIN")


# Add Worker configuration
USE_WORKER_URL = os.getenv("USE_WORKER_URL", "True").lower() == "true"
WORKER_URL = os.getenv("WORKER_URL")
WORKER_AUTH_KEY = os.getenv("WORKER_AUTH_KEY")

# Parse ALLOWED_HOSTS from environment variable
allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "")
if allowed_hosts_str:
    # Convert string representation to actual list
    import ast

    try:
        ALLOWED_HOSTS = ast.literal_eval(allowed_hosts_str)
    except (ValueError, SyntaxError):
        # Fallback if parsing fails
        ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.1.167"]
else:
    # Default if environment variable is not set
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.1.167"]
