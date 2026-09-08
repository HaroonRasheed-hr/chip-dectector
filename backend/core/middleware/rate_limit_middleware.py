import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger('core.middleware')

_RATE_LIMIT_PATHS: dict = getattr(settings, 'RATE_LIMIT_PATHS', {})


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        config = _RATE_LIMIT_PATHS.get(request.path)
        if config:
            ip = self._get_client_ip(request)
            cache_key = f'rl:{request.path}:{ip}'
            limit: int = config['limit']
            window: int = config['window']
            now = time.time()

            data = cache.get(cache_key)
            if data is None:
                cache.set(cache_key, {'count': 1, 'start': now}, timeout=window)
            elif now - data['start'] >= window:
                cache.set(cache_key, {'count': 1, 'start': now}, timeout=window)
            elif data['count'] >= limit:
                logger.warning('Rate limit hit: ip=%s path=%s', ip, request.path)
                return JsonResponse(
                    {'detail': 'Too many requests. Please try again later.'},
                    status=429,
                )
            else:
                data['count'] += 1
                cache.set(cache_key, data, timeout=window)

        return self.get_response(request)

    @staticmethod
    def _get_client_ip(request) -> str:
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
