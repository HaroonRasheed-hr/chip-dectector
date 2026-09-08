import os
from datetime import timedelta
from pathlib import Path

import environ

env = environ.Env(
    DEBUG=(bool, False),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    REFRESH_COOKIE_SECURE=(bool, False),
    MQTT_ENABLED=(bool, False),
    MQTT_PORT=(int, 1883),
    MQTT_KEEPALIVE=(int, 60),
    MQTT_QOS=(int, 1),
    MQTT_RECONNECT_MIN_DELAY=(int, 1),
    MQTT_RECONNECT_MAX_DELAY=(int, 60),
    MONITORING_ENABLED=(bool, True),
    MONITORING_INTERVAL_SECONDS=(int, 5),
    MONITORING_PUBLISH_TO_MQTT=(bool, True),
    INFERENCE_DEFAULT_CONFIDENCE_THRESHOLD=(float, 0.5),
    INFERENCE_CHIP_PHYSICAL_AREA_MM2=(float, 200.0),
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / 'frontend'
FRONTEND_BUILD_DIR = FRONTEND_DIR / 'out'
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '[::1]'])

LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
MEASUREMENTS_JSONL_PATH = BASE_DIR / 'core' / 'persistence' / 'measurements.jsonl'

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.users',
    'apps.inference',
    'apps.monitoring',
    'apps.calibration',
    'apps.mqtt_manager',
    'apps.websocket',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must come directly after SecurityMiddleware so it can
    # serve the collected Django static files AND the Next.js export
    # (mounted via STATICFILES_DIRS below) with proper cache headers.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.request_logging_middleware.RequestLoggingMiddleware',
    'core.middleware.authentication_middleware.JWTAuthCookieMiddleware',
    'core.middleware.rate_limit_middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Folders collected into STATIC_ROOT by `manage.py collectstatic`.
# `static/` keeps any project-owned static assets; the Next.js `_next/`
# folder is exposed at /_next/... by the catch-all view below, so we
# do NOT also expose it under /static/ to avoid duplication.
STATICFILES_DIRS = [
    p for p in [BASE_DIR / 'static'] if p.exists()
]

# Compressed (gzip/brotli) storage for Django's own static assets.
# `production.py` swaps this for the manifest variant so admin/DRF CSS
# gets content-addressed filenames behind a CDN.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── DRF ──────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env('JWT_ACCESS_TOKEN_LIFETIME_MINUTES')),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env('JWT_REFRESH_TOKEN_LIFETIME_DAYS')),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

JWT_REFRESH_COOKIE_NAME = 'refresh_token'
JWT_REFRESH_COOKIE_SECURE = env('REFRESH_COOKIE_SECURE')
JWT_REFRESH_COOKIE_HTTPONLY = True
JWT_REFRESH_COOKIE_SAMESITE = 'Lax'

# ── CORS ──────────────────────────────────────────────────────────────────────
# The frontend is served by this same Django process, so requests are
# same-origin by default. These entries only matter when the UI is run
# separately (e.g. `next dev` on :3000) or reached via the other loopback
# hostname than the one the API was called on.
_LOCAL_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=_LOCAL_ORIGINS)
CORS_ALLOW_CREDENTIALS = True

# Django requires the full origin (with scheme) for CSRF on POST requests
# coming from a browser page, for both loopback hostnames.
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=_LOCAL_ORIGINS)

# ── Rate limiting (path → {limit, window_seconds}) ───────────────────────────
RATE_LIMIT_PATHS = {
    '/api/auth/login/': {'limit': 5, 'window': 60},
    '/api/auth/register/': {'limit': 5, 'window': 60},
}

# ── Cache (used by rate limiter) ──────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'visionpulse-cache',
    }
}

# ── MQTT (Mosquitto) ─────────────────────────────────────────────────────────
MQTT = {
    'ENABLED': env('MQTT_ENABLED'),
    'HOST': env('MQTT_HOST', default='localhost'),
    'PORT': env('MQTT_PORT'),
    'USERNAME': env('MQTT_USERNAME', default=''),
    'PASSWORD': env('MQTT_PASSWORD', default=''),
    'CLIENT_ID': env('MQTT_CLIENT_ID', default='visionpulse-backend'),
    'KEEPALIVE': env('MQTT_KEEPALIVE'),
    'QOS': env('MQTT_QOS'),
    'RECONNECT_MIN_DELAY': env('MQTT_RECONNECT_MIN_DELAY'),
    'RECONNECT_MAX_DELAY': env('MQTT_RECONNECT_MAX_DELAY'),
}

# ── Monitoring ────────────────────────────────────────────────────────────────
MONITORING = {
    'ENABLED': env('MONITORING_ENABLED'),
    'INTERVAL_SECONDS': env('MONITORING_INTERVAL_SECONDS'),
    'PUBLISH_TO_MQTT': env('MONITORING_PUBLISH_TO_MQTT'),
}

# ── Inference ─────────────────────────────────────────────────────────────────
INFERENCE = {
    'DEFAULT_PROVIDER': env('INFERENCE_DEFAULT_PROVIDER', default='stub'),
    'DEFAULT_CONFIDENCE_THRESHOLD': env('INFERENCE_DEFAULT_CONFIDENCE_THRESHOLD'),
    'CHIP_PHYSICAL_AREA_MM2': env('INFERENCE_CHIP_PHYSICAL_AREA_MM2'),
    'DEFAULT_LINE_ID': env('INFERENCE_DEFAULT_LINE_ID', default='line-1'),
    'DEFAULT_STATION_ID': env('INFERENCE_DEFAULT_STATION_ID', default='station-1'),
}

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
        # The MQTT result log is line-delimited JSON. The helper module
        # `core.logging_system.mqtt_result_logger` already constructs the
        # full JSON document (including its own timestamp), so this
        # formatter just passes the message through unchanged.
        'json_event': {
            'format': '{message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'runtime_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'runtime.log'),
            'formatter': 'verbose',
        },
        'errors_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'errors.log'),
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'inference_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'inference.log'),
            'formatter': 'verbose',
        },
        'warnings_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'warnings.log'),
            'formatter': 'verbose',
            'level': 'WARNING',
        },
        'mqtt_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'mqtt.log'),
            'formatter': 'verbose',
        },
        # Structured result feed: one JSON object per line, flushed on
        # every record so external tail/monitoring tools see new
        # publishes and receives within milliseconds.
        'mqtt_result_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'mqtt-result.log'),
            'formatter': 'json_event',
        },
    },
    'loggers': {
        # Runtime — general application events
        'visionpulse.runtime': {
            'handlers': ['console', 'runtime_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Errors — every captured error across all domains
        'visionpulse.errors': {
            'handlers': ['console', 'errors_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Inference — model/pipeline diagnostics
        'visionpulse.inference': {
            'handlers': ['console', 'inference_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Warnings — non-critical issues
        'visionpulse.warnings': {
            'handlers': ['console', 'warnings_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        # MQTT — every MQTT event lands in mqtt.log. Severity-level
        # handlers (errors_file with level=ERROR, warnings_file with
        # level=WARNING) also mirror ERROR/WARNING messages into the
        # cross-domain audit files, so the unified error log stays
        # authoritative.
        'visionpulse.mqtt': {
            'handlers': ['console', 'mqtt_file', 'warnings_file', 'errors_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Dedicated structured feed for every publish / subscribe /
        # connection event. `propagate=False` keeps these JSON records
        # out of mqtt.log / runtime.log / warnings.log so each file
        # stays single-purpose.
        'visionpulse.mqtt.result': {
            'handlers': ['mqtt_result_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.users': {
            'handlers': ['console', 'runtime_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.middleware': {
            'handlers': ['console', 'runtime_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
