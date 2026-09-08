from .base import *  # noqa: F401, F403

DEBUG = False

JWT_REFRESH_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Hashed filenames + long Cache-Control for admin/DRF static assets.
STORAGES['staticfiles'] = {  # noqa: F405
    'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
}
