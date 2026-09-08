from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from core.views.frontend import serve_frontend, serve_index

# Path prefixes that belong to the Django backend itself. The frontend
# catch-all must NEVER swallow these, otherwise API requests would
# return HTML instead of JSON.
_RESERVED_PREFIXES = ("api/", "admin/", "static/", "media/")
_RESERVED_PATTERN = r"^(?P<path>(?!(?:{})).*)$".format(
    "|".join(p.replace("/", r"\/") for p in _RESERVED_PREFIXES)
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/inference/', include('apps.inference.urls')),
    path('api/monitoring/', include('apps.monitoring.urls')),
]

# Serve user-uploaded media through Django when DEBUG is on; in
# production this should be fronted by the web server / CDN, but
# WhiteNoise can also handle it via STATICFILES_DIRS if needed.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Frontend (Next.js static export). Order matters: the catch-all has to
# come last so the reserved API/admin/static/media prefixes match first.
urlpatterns += [
    path('', serve_index, name='frontend-index'),
    re_path(_RESERVED_PATTERN, serve_frontend, name='frontend-catchall'),
]
