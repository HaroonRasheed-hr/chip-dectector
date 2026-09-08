from .base import *  # noqa: F401, F403
from pathlib import Path

DEBUG = True

# SQLite for local development — switch to DATABASE_URL in production
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

JWT_REFRESH_COOKIE_SECURE = False
