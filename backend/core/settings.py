"""
Django settings for Client Beat project.
"""
import os
import sys
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR

env = environ.Env()
env.read_env(str(PROJECT_ROOT.parent / '.env'), overwrite=False)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-insecure-change-me-please-1234567890')
DEBUG = env.bool('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['*'])
if DEBUG:
    ALLOWED_HOSTS.extend(['testserver', 'localhost', '127.0.0.1', '0.0.0.0'])
ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))

sys.path.insert(0, str(BASE_DIR / 'apps'))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'django_htmx',
    'widget_tweaks',
    'django_celery_results',
    'django_celery_beat',
    'apps.accounts',
    'apps.geo',
    'apps.businesses',
    'apps.billing',
    'apps.encuestas',
    'apps.reputation',
    'apps.surveys',
    'apps.sentiment',
    'apps.pages',
    'apps.adminpanel',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'apps.businesses.middleware.tenant.TenantMiddleware',
]

ROOT_URLCONF = 'core.urls'

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
                'apps.pages.context_processors.client_empresa',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

DATABASES = {
    'default': env.db_url(
        'DATABASE_URL',
        default='sqlite:///db.sqlite3'
    )
}
DATABASES['default']['CONN_MAX_AGE'] = 600 if not DEBUG else 0
if 'postgresql' in DATABASES['default'].get('ENGINE', ''):
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
DEFAULT_CHARSET = 'utf-8'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = 'd/m/Y'
SHORT_DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
USE_THOUSAND_SEPARATOR = False

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REDIS_URL = env.str('REDIS_URL', default='')
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL or 'redis://localhost:6379/0',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5 if not DEBUG else None,
            "SOCKET_TIMEOUT": 5 if not DEBUG else None,
        },
        "KEY_PREFIX": "clientbeat",
    } if REDIS_URL and (
        REDIS_URL.startswith('redis://localhost') or REDIS_URL.startswith('redis://127.0.0.1')
    ) else {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='contacto@avaapp.cl')

FLOW_API_KEY = env('FLOW_API_KEY', default='')
FLOW_SECRET_KEY = env('FLOW_SECRET_KEY', default='')
FLOW_ENVIRONMENT = env('FLOW_ENVIRONMENT', default='sandbox')
FLOW_WEBHOOK_SECRET = env('FLOW_WEBHOOK_SECRET', default='')

GOOGLE_PLACES_API_KEY = env('GOOGLE_PLACES_API_KEY', default='')

EMPRESA = {
    'NOMBRE': env('EMPRESA_NOMBRE', default='Client Beat SpA'),
    'RUT': env('EMPRESA_RUT', default='77.607.311-3'),
    'DOMICILIO': env('EMPRESA_DOMICILIO', default='Asturias 790 E, Rancagua'),
    'CONTACTO': env('EMPRESA_CONTACTO', default='contacto@avaapp.cl'),
    'SITIO_WEB': env('EMPRESA_SITIO_WEB', default='www.clientbeat.cl'),
}

SITE_ID = 1

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'clientbeat': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
