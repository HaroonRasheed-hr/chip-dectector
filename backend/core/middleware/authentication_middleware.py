class JWTAuthCookieMiddleware:
    """
    Injects the access token from an 'access_token' cookie into the
    Authorization header when no header is already present. This lets
    cookie-capable clients (SSR, test suites) authenticate without manually
    setting headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.META.get('HTTP_AUTHORIZATION'):
            access_token = request.COOKIES.get('access_token')
            if access_token:
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        return self.get_response(request)
