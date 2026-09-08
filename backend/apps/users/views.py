import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users import services
from apps.users.serializers import LoginSerializer, RegisterSerializer
from apps.users.services import AuthenticationError

logger = logging.getLogger('apps.users')

_COOKIE = settings.JWT_REFRESH_COOKIE_NAME
_COOKIE_MAX_AGE = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE,
        value=token,
        httponly=settings.JWT_REFRESH_COOKIE_HTTPONLY,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        max_age=_COOKIE_MAX_AGE,
        path='/',
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE, path='/')


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = services.register_user(serializer.validated_data)
        return Response({'user': user_data}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.authenticate_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
        except AuthenticationError as exc:
            return Response(
                {'detail': str(exc), 'code': exc.code},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = services.generate_tokens(user)
        response = Response({
            'access': tokens['access'],
            'user': services.get_user_info(user),
        })
        _set_refresh_cookie(response, tokens['refresh'])
        logger.info('User logged in: %s', user.email)
        return response


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh_token = request.COOKIES.get(_COOKIE)
        if refresh_token:
            try:
                services.blacklist_refresh_token(refresh_token)
            except ValueError:
                pass  # Already invalid/blacklisted — still clear the cookie
        response = Response({'detail': 'Logged out successfully.'})
        _clear_refresh_cookie(response)
        logger.info('User logged out: %s', request.user.email)
        return response


class TokenRefreshView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        refresh_token = request.COOKIES.get(_COOKIE)
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            tokens = services.rotate_refresh_token(refresh_token)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'access': tokens['access']})
        _set_refresh_cookie(response, tokens['refresh'])
        return response


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(services.get_user_info(request.user))
