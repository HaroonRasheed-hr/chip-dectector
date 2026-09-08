import logging

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers import UserSerializer

logger = logging.getLogger('apps.users')


def register_user(validated_data: dict) -> dict:
    user = User.objects.create_user(
        email=validated_data['email'],
        full_name=validated_data['full_name'],
        password=validated_data['password'],
    )
    logger.info('New user registered: %s', user.email)
    return UserSerializer(user).data


class AuthenticationError(ValueError):
    """Login failure with a machine-readable code the API layer can map to a response."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def authenticate_user(email: str, password: str) -> User:
    normalized_email = email.lower().strip()
    try:
        user = User.objects.get(email=normalized_email)
    except User.DoesNotExist:
        raise AuthenticationError(
            'user_not_found',
            'User does not exist, please sign up first.',
        )

    if not user.check_password(password):
        raise AuthenticationError('invalid_password', 'Incorrect Password')

    if not user.is_active:
        raise AuthenticationError('account_disabled', 'Account is disabled.')

    return user


def generate_tokens(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def blacklist_refresh_token(refresh_token_str: str) -> None:
    try:
        token = RefreshToken(refresh_token_str)
        token.blacklist()
    except TokenError as exc:
        raise ValueError('Invalid or expired refresh token.') from exc


def rotate_refresh_token(refresh_token_str: str) -> dict:
    """Validate, blacklist the old refresh token, and issue a fresh token pair."""
    try:
        old_token = RefreshToken(refresh_token_str)
        user_id = old_token['user_id']
        user = User.objects.get(id=user_id)
        old_token.blacklist()
        return generate_tokens(user)
    except (TokenError, User.DoesNotExist) as exc:
        raise ValueError('Invalid or expired refresh token.') from exc


def get_user_info(user: User) -> dict:
    return UserSerializer(user).data
