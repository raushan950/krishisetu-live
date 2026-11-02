"""
Django settings for krishisetu project.
Configured for KrishiSetu (SIH26132) - Production & Local.
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Render injects RENDER=true for every service. Default DEBUG off there.
IS_RENDER = bool(os.getenv('RENDER') or os.getenv('RENDER_EXTERNAL_HOSTNAME'))
DEBUG = os.getenv('DEBUG', 'False' if IS_RENDER else 'True').lower() in ('true', '1', 't')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG and not IS_RENDER:
        SECRET_KEY = 'django-insecure-dev-fallback-key-krishisetu'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set via environment variables in production.')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]

# Render external hostname support
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Wildcard for onrender.com subdomains
ALLOWED_HOSTS.append('.onrender.com')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Local KrishiSetu apps
    'apps.accounts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be at the top of middleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise for static asset serving on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'krishisetu.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'krishisetu.wsgi.application'


# Custom User Model (Must be set before initial database migrations)
AUTH_USER_MODEL = 'accounts.CustomUser'


# Database Configuration: Supports Render DATABASE_URL or Local PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'krishisetu_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }

# Isolated in-memory SQLite for `manage.py test` so CI/local tests do not need PostgreSQL.
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# Static and Media Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}


# SimpleJWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}


# CORS Configuration for React Frontend (Supports local & Vercel deployments)
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,https://instant-geode-9y9nkbl.tmp.now,https://instant-geode-9y9nkbl-raushan-kumars-projects-fed41dec.vercel.app'
    ).split(',') if origin.strip()
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/.*\.vercel\.app$",
    r"^https:\/\/.*\.tmp\.now$",
    r"^http:\/\/localhost:\d+$",
    r"^http:\/\/127\.0\.0\.1:\d+$",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'https://*.onrender.com,https://*.vercel.app,https://*.tmp.now,http://localhost:5173,http://127.0.0.1:5173'
    ).split(',') if origin.strip()
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
if IS_RENDER:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
