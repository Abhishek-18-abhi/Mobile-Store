"""
Django settings for mobile_store project.
"""
import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

# Project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env.local")

# Security settings
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-prod-key-for-mobile-store")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Neon Authentication Configuration (optional)
NEON_AUTH_BASE_URL = os.getenv("NEON_AUTH_BASE_URL", "")
NEON_AUTH_JWKS_URL = os.getenv("NEON_AUTH_JWKS_URL", "")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
    ".vercel.app",
    ".now.sh",
    "*",
]
if os.getenv("VERCEL_URL"):
    ALLOWED_HOSTS.append(os.getenv("VERCEL_URL"))

# Application definition

INSTALLED_APPS = [
    # Django built-in apps (REQUIRED)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Your apps
    'accounts',
    'products',
    'orders',
    'payment',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',           # CORS — must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mobile_store.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'orders.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'mobile_store.wsgi.application'

# Database — Neon PostgreSQL
_raw_db_url = os.environ.get("DATABASE_URL", "").strip().strip('"').strip("'")
if _raw_db_url:
    os.environ["DATABASE_URL"] = _raw_db_url
    DATABASES = {
        "default": dj_database_url.parse(
            _raw_db_url,
            conn_max_age=0,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=0,
            ssl_require=True,
        )
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'

# Use writable /tmp directory on Vercel serverless to prevent Errno 30 Read-only filesystem error
if os.environ.get('VERCEL') or not os.access(BASE_DIR, os.W_OK):
    MEDIA_ROOT = Path('/tmp') / 'media'
else:
    MEDIA_ROOT = BASE_DIR / 'media'

try:
    os.makedirs(MEDIA_ROOT / 'products', exist_ok=True)
except Exception:
    pass

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Default primary key field type (avoids Django warning)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS — allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# CSRF trusted origins for Vercel deployment
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.now.sh',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]
if os.getenv('VERCEL_URL'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.getenv('VERCEL_URL')}")

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Django session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14

CSRF_COOKIE_SAMESITE = "Lax"

# Email Configuration (SMTP with Console/Logging Fallback)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'MobileStore <no-reply@mobilestore.com>')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
