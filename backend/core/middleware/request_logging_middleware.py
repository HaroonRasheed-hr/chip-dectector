import logging
import time

logger = logging.getLogger('core.middleware')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        user = getattr(request, 'user', None)
        user_label = user.email if (user and user.is_authenticated) else 'anonymous'

        logger.info(
            '%s %s %s %sms user=%s ip=%s',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            user_label,
            self._get_client_ip(request),
        )
        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
