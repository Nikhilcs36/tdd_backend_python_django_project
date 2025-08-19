from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')
USERS_URL = reverse('user:users')
LOGOUT_URL = reverse('user:logout')


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user with a valid payload is successful."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.username, payload['username'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',

        )

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if the password is too short."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pw',
            'passwordRepeat': 'pw',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = User.objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_user_with_password_repeat_success(self):
        """Test creating a user with a valid payload including
        passwordRepeat is successful."""
        payload = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.username, payload['username'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertNotIn('passwordRepeat', res.data)

    def test_create_user_with_mismatched_password_error(self):
        """Test error returned if password and passwordRepeat do not match."""
        payload = {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'password123',
            'passwordRepeat': 'password124',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_blank_username_error(self):
        """Test error returned if username is blank."""
        payload = {
            'username': '',
            'email': 'test4@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        """Test that a token is created for the user."""
        user_details = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        }
        User.objects.create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], user_details['username'])
        self.assertEqual(res.data['email'], user_details['email'])

    def test_create_token_bad_credentials(self):
        """Test that a token is not created with bad credentials."""
        user_details = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        }
        User.objects.create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': 'badpassword',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('access', res.data)
        self.assertNotIn('refresh', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtains_pair_view_uses_custom_serializer(self):
        """Test that TokenObtainPairView is using the custom serializer."""
        from user.views import CustomTokenObtainPairView
        from user.serializers import CustomTokenObtainPairSerializer
        self.assertEqual(
            CustomTokenObtainPairView.serializer_class,
            CustomTokenObtainPairSerializer
        )


class PrivateUserApiTests(TestCase):
    """Test the private features of the user API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            username='testuser'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'username': self.user.username,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me endpoint."""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_refresh_token(self):
        """Test that a refresh token can be used to get a new access token."""
        user_details = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'password123',
        }
        User.objects.create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        refresh_token = res.data['refresh']

        refresh_payload = {'refresh': refresh_token}
        res = self.client.post(reverse('user:token_refresh'), refresh_payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_invalid_refresh_token(self):
        """Test that an invalid refresh token is rejected."""
        refresh_payload = {'refresh': 'invalid_token'}
        res = self.client.post(reverse('user:token_refresh'), refresh_payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_with_token(self):
        """Test accessing a protected endpoint with a valid token."""
        user_details = {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'password123',
        }
        user = User.objects.create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        access_token = res.data['access']

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'JWT {access_token}')
        res = client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], user.email)

    def test_unauthenticated_access_to_protected_endpoint(self):
        """Test that an unauthenticated user cannot access
            a protected endpoint."""
        client = APIClient()
        res = client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_user(self):
        """Test partial update of the user profile."""
        original_email = 'test_partial_update@example.com'
        user = User.objects.create_user(
            email=original_email,
            password='password123',
            username='testuser_partial_update'
        )
        self.client.force_authenticate(user=user)

        payload = {'username': 'newusername'}
        res = self.client.put(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, payload['username'])
        self.assertEqual(user.email, original_email)

    def test_user_email_not_updated(self):
        """Test that the email address cannot be updated."""
        original_email = 'test_email_not_updated@example.com'
        user = User.objects.create_user(
            email=original_email,
            password='password123',
            username='testuser_email_not_updated'
        )
        self.client.force_authenticate(user=user)

        payload = {'email': 'newemail@example.com'}
        res = self.client.put(ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.email, original_email)

    def test_list_users_for_non_admin_user_fail(self):
        """Test that non-admin users cannot list users."""
        res = self.client.get(USERS_URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_specific_user_detail_for_non_admin_fail(self):
        """Test retrieving a specific user's details for non-admin fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_for_non_admin_fail(self):
        """Test updating a user for non-admin fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        payload = {'username': 'newusername'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserApiTests(TestCase):
    """Test the admin features of the user API."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            username='adminuser'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_users_list_success(self):
        """Test retrieving a list of users for admin."""
        User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        User.objects.create_user(
            email='test3@example.com',
            password='password123',
            username='testuser3'
        )

        res = self.client.get(USERS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(res.data[0]['username'], self.user.username)
        self.assertEqual(res.data[1]['username'], 'testuser2')
        self.assertEqual(res.data[2]['username'], 'testuser3')

    def test_retrieve_specific_user_detail_success(self):
        """Test retrieving a specific user's details for admin."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], user.username)

    def test_delete_user_success(self):
        """Test deleting a user for admin."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user.id).exists())

    def test_update_user_success(self):
        """Test updating a user for admin."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        payload = {'username': 'newusername'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, payload['username'])


class StaffUserApiTests(TestCase):
    """Test the staff features of the user API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='staff@example.com',
            password='password123',
            username='staffuser',
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_users_for_staff_user_success(self):
        """Test that staff users can list users."""
        res = self.client.get(USERS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_specific_user_detail_for_staff_fail(self):
        """Test retrieving a specific user's details for staff fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_for_staff_fail(self):
        """Test deleting a user for staff fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_for_staff_fail(self):
        """Test updating a user for staff fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        payload = {'username': 'newusername'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_blacklists_refresh_token(self):
        """Test that logging out blacklists the refresh token."""
        refresh = RefreshToken.for_user(self.user)

        payload = {'refresh': str(refresh)}
        res = self.client.post(LOGOUT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        is_blacklisted = BlacklistedToken.objects.filter(
            token__token=str(refresh)
        ).exists()
        self.assertTrue(is_blacklisted)

    def test_logout_with_invalid_token(self):
        """Test that logging out with an invalid token returns an error."""
        payload = {'refresh': 'invalid_token'}
        res = self.client.post(LOGOUT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_refresh_token(self):
        """Test that logging out requires a refresh token."""
        res = self.client.post(LOGOUT_URL, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
