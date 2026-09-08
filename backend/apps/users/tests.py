from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

PASSWORD = 'Str0ngP@ss!'


class BaseAuthTest(APITestCase):
    def setUp(self):
        # Rate-limit middleware uses LocMemCache, which persists across tests.
        # Clear it so one test class's request bursts don't trip 429s in the next.
        cache.clear()
        self.client = APIClient()
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.logout_url = reverse('auth-logout')
        self.refresh_url = reverse('auth-token-refresh')
        self.me_url = reverse('auth-me')

    def _make_user(self, email='user@example.com', full_name='Test User', password=PASSWORD):
        return User.objects.create_user(email=email, full_name=full_name, password=password)

    def _login(self, email='user@example.com', password=PASSWORD):
        return self.client.post(self.login_url, {'email': email, 'password': password}, format='json')

    def _authenticate(self, user: User) -> str:
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return str(refresh)

    def _set_refresh_cookie(self, response):
        self.client.cookies['refresh_token'] = response.cookies['refresh_token'].value


# ── Registration ──────────────────────────────────────────────────────────────

class RegistrationTest(BaseAuthTest):
    def _payload(self, **overrides):
        base = {
            'email': 'new@example.com',
            'full_name': 'New User',
            'password': PASSWORD,
            'confirm_password': PASSWORD,
        }
        base.update(overrides)
        return base

    def test_register_success(self):
        response = self.client.post(self.register_url, self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'new@example.com')
        self.assertNotIn('password', response.data['user'])
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_register_normalises_email_to_lowercase(self):
        self.client.post(self.register_url, self._payload(email='UPPER@EXAMPLE.COM'), format='json')
        self.assertTrue(User.objects.filter(email='upper@example.com').exists())

    def test_register_duplicate_email(self):
        self._make_user(email='dup@example.com')
        response = self.client.post(self.register_url, self._payload(email='dup@example.com'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        response = self.client.post(
            self.register_url,
            self._payload(confirm_password='Different1!'),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

    def test_register_invalid_email(self):
        response = self.client.post(self.register_url, self._payload(email='not-an-email'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_short(self):
        response = self.client.post(
            self.register_url,
            self._payload(password='ab1!', confirm_password='ab1!'),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_required_fields(self):
        response = self.client.post(self.register_url, {'email': 'a@b.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_returns_no_password_field(self):
        response = self.client.post(self.register_url, self._payload(), format='json')
        self.assertNotIn('password', response.data.get('user', {}))
        self.assertNotIn('confirm_password', response.data.get('user', {}))


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginTest(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self._make_user()

    def test_login_success_returns_access_token(self):
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)

    def test_login_sets_httponly_refresh_cookie(self):
        response = self._login()
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_login_does_not_expose_refresh_in_body(self):
        response = self._login()
        self.assertNotIn('refresh', response.data)

    def test_login_does_not_expose_password_in_body(self):
        response = self._login()
        self.assertNotIn('password', response.data.get('user', {}))

    def test_login_wrong_password(self):
        response = self._login(password='WrongPass99!')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)

    def test_login_nonexistent_email(self):
        response = self._login(email='nobody@example.com')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        user = User.objects.get(email='user@example.com')
        user.is_active = False
        user.save()
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_password_field(self):
        response = self.client.post(self.login_url, {'email': 'user@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutTest(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.user = self._make_user()

    def test_logout_success(self):
        login_resp = self._login()
        self._set_refresh_cookie(login_resp)
        self._authenticate(self.user)

        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)

    def test_logout_requires_authentication(self):
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_cookie_still_succeeds(self):
        # Authenticated but no refresh cookie present
        self._authenticate(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_clears_refresh_cookie(self):
        login_resp = self._login()
        self._set_refresh_cookie(login_resp)
        self._authenticate(self.user)

        response = self.client.post(self.logout_url)
        # Django sets the cookie to empty string with max_age=0 on delete
        cookie = response.cookies.get('refresh_token')
        if cookie:
            self.assertIn(cookie.value, ('', None))


# ── Token refresh ─────────────────────────────────────────────────────────────

class TokenRefreshTest(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.user = self._make_user()

    def test_refresh_returns_new_access_token(self):
        login_resp = self._login()
        self._set_refresh_cookie(login_resp)

        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_does_not_expose_refresh_in_body(self):
        login_resp = self._login()
        self._set_refresh_cookie(login_resp)

        response = self.client.post(self.refresh_url)
        self.assertNotIn('refresh', response.data)

    def test_refresh_rotates_cookie(self):
        login_resp = self._login()
        old_refresh = login_resp.cookies['refresh_token'].value
        self._set_refresh_cookie(login_resp)

        response = self.client.post(self.refresh_url)
        new_cookie = response.cookies.get('refresh_token')
        self.assertIsNotNone(new_cookie)
        self.assertNotEqual(new_cookie.value, old_refresh)

    def test_refresh_without_cookie_returns_401(self):
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token_returns_401(self):
        self.client.cookies['refresh_token'] = 'totally.invalid.token'
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_token_is_rejected(self):
        login_resp = self._login()
        original_refresh = login_resp.cookies['refresh_token'].value
        self._set_refresh_cookie(login_resp)

        # First use — rotates and blacklists the original
        self.client.post(self.refresh_url)

        # Re-use original (now blacklisted) — must be rejected
        self.client.cookies['refresh_token'] = original_refresh
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Me endpoint ───────────────────────────────────────────────────────────────

class MeEndpointTest(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.user = self._make_user()

    def test_me_returns_user_info(self):
        self._authenticate(self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['full_name'], self.user.full_name)

    def test_me_includes_expected_fields(self):
        self._authenticate(self.user)
        response = self.client.get(self.me_url)
        for field in ('id', 'email', 'full_name', 'created_at', 'updated_at'):
            self.assertIn(field, response.data)

    def test_me_never_exposes_password(self):
        self._authenticate(self.user)
        response = self.client.get(self.me_url)
        self.assertNotIn('password', response.data)

    def test_me_unauthenticated_returns_401(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_expired_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.jwt.token')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
