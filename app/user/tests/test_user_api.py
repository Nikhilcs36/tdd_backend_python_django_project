from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.conf import settings
import os
import tempfile


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
            'password': 'Password123',
            'passwordRepeat': 'Password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload['email'])
        self.assertEqual(user.username, payload['username'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertIsNotNone(user.id)  # Verify ID field exists
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
            'passwordRepeat': 'Password123',

        }
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123',

        )

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)
        self.assertEqual(res.data['email'][0], 'E-mail in use')

    def test_user_with_username_exists_error(self):
        """Test error returned if user with username exists."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
            'passwordRepeat': 'Password123',
        }
        User.objects.create_user(
            username='testuser',
            email='test2@example.com',
            password='Password123',
        )

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res.data)
        self.assertEqual(res.data['username'][0], 'Username already exists')

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
            'password': 'Password123',
            'passwordRepeat': 'Password123',

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
            'password': 'Password123',
            'passwordRepeat': 'Password124',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('passwordRepeat', res.data)
        self.assertEqual(res.data['passwordRepeat']
                         [0], 'password_mismatch')

    def test_create_user_with_null_password_repeat_error(self):
        """Test error returned if passwordRepeat is null."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
            'passwordRepeat': '',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('passwordRepeat', res.data)
        self.assertEqual(res.data['passwordRepeat']
                         [0], 'password_repeat_null')

    def test_create_user_with_blank_username_error(self):
        """Test error returned if username is blank."""
        payload = {
            'username': '',
            'email': 'test4@example.com',
            'password': 'Password123',
            'passwordRepeat': 'Password123',

        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res.data)
        self.assertEqual(res.data['username'][0], 'Username cannot be null')

    def test_create_user_with_blank_email_error(self):
        """Test error returned if email is blank."""
        payload = {
            'username': 'testuser',
            'email': '',
            'password': 'Password123',
            'passwordRepeat': 'Password123',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)
        self.assertEqual(res.data['email'][0], 'E-mail cannot be null')

    def test_create_user_with_invalid_username_error(self):
        """Test error returned if username is invalid."""
        # Test for username too short
        payload_short = {
            'username': 'usr',
            'email': 'test5@example.com',
            'password': 'Password123',
            'passwordRepeat': 'Password123',
        }
        res_short = self.client.post(CREATE_USER_URL, payload_short)
        self.assertEqual(res_short.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res_short.data)
        self.assertEqual(
            res_short.data['username'][0],
            'Must have min 4 and max 32 characters'
        )

        # Test for username too long
        payload_long = {
            'username': 'a' * 33,
            'email': 'test6@example.com',
            'password': 'Password123',
            'passwordRepeat': 'Password123',
        }
        res_long = self.client.post(CREATE_USER_URL, payload_long)
        self.assertEqual(res_long.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res_long.data)
        self.assertEqual(res_long.data['username'][0],
                         'Must have min 4 and max 32 characters')

    def test_create_user_with_invalid_email_error(self):
        """Test error returned if email is invalid."""
        payload = {
            'username': 'testuser7',
            'email': 'invalid-email',
            'password': 'Password123',
            'passwordRepeat': 'Password123',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', 'email' in res.data and res.data or {})
        self.assertEqual(
            res.data['email'][0],
            'E-mail is not valid'
        )

    def test_invalid_email_no_duplicate_error_messages(self):
        """Test invalid email validation doesn't show duplicate errors."""
        payload = {
            'username': 'testuser',
            'email': 'invalid-email',  # Invalid email format
            'password': 'Password123',
            'passwordRepeat': 'Password123',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

        # Check that the error message appears only once, not duplicated
        email_errors = res.data['email']
        self.assertEqual(len(email_errors), 1)
        self.assertEqual(email_errors[0], 'E-mail is not valid')

    def test_create_user_with_invalid_password_error(self):
        """Test error returned if password does not meet complexity
        requirements."""
        # Test for password without uppercase letter
        payload_no_upper = {
            'username': 'testuser8',
            'email': 'test8@example.com',
            'password': 'password123',
            'passwordRepeat': 'password123',
        }
        res_no_upper = self.client.post(CREATE_USER_URL, payload_no_upper)
        self.assertEqual(res_no_upper.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res_no_upper.data)
        self.assertEqual(
            res_no_upper.data['password'][0],
            ('Password must have at least 1 uppercase, '
             '1 lowercase letter and 1 number')
        )

        # Test for password without lowercase letter
        payload_no_lower = {
            'username': 'testuser9',
            'email': 'test9@example.com',
            'password': 'PASSWORD123',
            'passwordRepeat': 'PASSWORD123',
        }
        res_no_lower = self.client.post(CREATE_USER_URL, payload_no_lower)
        self.assertEqual(res_no_lower.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res_no_lower.data)
        self.assertEqual(
            res_no_lower.data['password'][0],
            ('Password must have at least 1 uppercase, '
             '1 lowercase letter and 1 number')
        )

        # Test for password without number
        payload_no_number = {
            'username': 'testuser10',
            'email': 'test10@example.com',
            'password': 'Password',
            'passwordRepeat': 'Password',
        }
        res_no_number = self.client.post(CREATE_USER_URL, payload_no_number)
        self.assertEqual(res_no_number.status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res_no_number.data)
        self.assertEqual(
            res_no_number.data['password'][0],
            ('Password must have at least 1 uppercase, '
             '1 lowercase letter and 1 number')
        )

    def test_create_token_for_user(self):
        """Test that a token is created for the user."""
        user_details = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
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
        self.assertEqual(res.data['id'], User.objects.get(
            email=user_details['email']).id)
        self.assertEqual(res.data['username'], user_details['username'])
        self.assertEqual(res.data['email'], user_details['email'])

    def test_create_token_bad_credentials(self):
        """Test that a token is not created with bad credentials."""
        user_details = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
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

    def test_create_user_with_null_password_error(self):
        """Test error returned if password is null."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '',
            'passwordRepeat': 'Password123',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)
        # Should show custom error message "Password cannot be null"
        # instead of Django default "This field may not be blank."
        self.assertEqual(res.data['password'][0], 'Password cannot be null')

    def test_create_user_with_short_password_error(self):
        """Test error returned if password is too short."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pass',
            'passwordRepeat': 'pass',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)
        # Should show custom error message
        # "Password must have at least 6 characters"
        self.assertEqual(
            res.data['password'][0],
            'Password must have at least 6 characters'
        )

    def test_create_user_with_invalid_password_complexity_error(self):
        """Test error returned if password lacks complexity requirements."""
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password',  # No uppercase or number
            'passwordRepeat': 'password',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data)
        # Should show custom error message
        # "Password must have at least 1 uppercase,"
        # "1 lowercase letter and 1 number"
        self.assertEqual(
            res.data['password'][0],
            'Password must have at least 1 uppercase, '
            '1 lowercase letter and 1 number'
        )


class PrivateUserApiTests(TestCase):
    """Test the private features of the user API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='Password123',
            username='testuser'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.user.refresh_from_db()
        if self.user.image:
            image_path = self.user.image.path
            if os.path.exists(image_path):
                os.remove(image_path)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'image': None,
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
            'password': 'Password123',
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
            'password': 'Password123',
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
            password='Password123',
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
            password='Password123',
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
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_for_non_admin_fail(self):
        """Test updating a user for non-admin fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        payload = {'username': 'newusername'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_image_to_user_profile_with_existing_image_success(self):
        """Test uploading an existing image to the user profile."""
        image_path = os.path.join(
            settings.MEDIA_ROOT, 'uploads', 'user', '29-png.png'
        )
        with open(image_path, 'rb') as image_file:
            payload = {'image': image_file}
            res = self.client.patch(
                ME_URL, payload, format='multipart'
            )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.user.image.path))

    def test_upload_image_invalid_file_type_fail(self):
        """Test uploading an invalid file type for the user profile."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
            temp_file.write(b'not an image')
            temp_file.seek(0)
            payload = {'image': temp_file}
            res = self.client.patch(
                ME_URL, payload, format='multipart'
            )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', res.data)
        self.assertEqual(
            res.data['image'][0],
            'Invalid image format. Only JPG, JPEG, and PNG are allowed.'
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.image)

    def test_image_url_is_absolute(self):
        """Test that the image URL in the response is an absolute URL."""
        image_path = os.path.join(
            settings.MEDIA_ROOT, 'uploads', 'user', '29-png.png'
        )
        with open(image_path, 'rb') as image_file:
            payload = {'image': image_file}
            res = self.client.patch(
                ME_URL, payload, format='multipart'
            )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(res.data['image'].startswith('http'))

    def test_upload_image_too_large_fail(self):
        """Test uploading an image that is too large."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Create a file that is larger than the MAX_UPLOAD_SIZE
        large_file_content = b'a' * (settings.MAX_UPLOAD_SIZE + 1)
        image = SimpleUploadedFile(
            "large_image.png", large_file_content, content_type="image/png"
        )
        payload = {'image': image}
        res = self.client.patch(
            ME_URL, payload, format='multipart'
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data, {
            "image": [
                "Image size cannot exceed 2097152 bytes."
            ]
        })

    def test_clear_user_image_success(self):
        """Test clearing the user's profile image."""
        image_path = os.path.join(
            settings.MEDIA_ROOT, 'uploads', 'user', '31-png.png'
        )
        with open(image_path, 'rb') as image_file:
            payload = {'image': image_file}
            res = self.client.patch(
                ME_URL, payload, format='multipart'
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.image)

        # Now, clear the image
        payload = {'image': ''}
        res = self.client.patch(ME_URL, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.image)

    def test_replace_user_image_deletes_old_file(self):
        """Test that replacing a user's image deletes the old image file."""
        # Upload first image
        first_image_path = os.path.join(
            settings.MEDIA_ROOT, 'uploads', 'user', '31-png.png'
        )
        with open(first_image_path, 'rb') as first_image_file:
            payload = {'image': first_image_file}
            res = self.client.patch(
                ME_URL, payload, format='multipart'
            )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.image)

        # Store the path of the first uploaded image
        first_uploaded_image_path = self.user.image.path
        self.assertTrue(os.path.exists(first_uploaded_image_path))

        # Upload second image (replace the first one)
        second_image_path = os.path.join(
            settings.MEDIA_ROOT, 'uploads', 'user', '45-png.png'
        )
        with open(second_image_path, 'rb') as second_image_file:
            payload = {'image': second_image_file}
            res = self.client.patch(
                ME_URL, payload, format='multipart'
            )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.image)

        # Verify the old image file was deleted from filesystem
        self.assertFalse(os.path.exists(first_uploaded_image_path))

        # Verify the new image file exists
        self.assertTrue(os.path.exists(self.user.image.path))
        self.assertNotEqual(self.user.image.path, first_uploaded_image_path)


class AdminUserApiTests(TestCase):
    """Test the admin features of the user API."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email='admin@example.com',
            password='Password123',
            username='adminuser'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_users_list_success(self):
        """Test retrieving a list of users for admin."""
        User.objects.create_user(
            email='test2@example.com',
            password='Password123',
            username='testuser2'
        )
        User.objects.create_user(
            email='test3@example.com',
            password='Password123',
            username='testuser3'
        )

        res = self.client.get(USERS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # With pagination, response structure changes to include metadata
        self.assertEqual(len(res.data['results']), 3)
        self.assertEqual(
            res.data['results'][0]['username'], self.user.username
        )
        self.assertEqual(res.data['results'][1]['username'], 'testuser2')
        self.assertEqual(res.data['results'][2]['username'], 'testuser3')
        self.assertEqual(res.data['count'], 3)
        self.assertIsNone(res.data['previous'])
        self.assertIsNone(res.data['next'])

    def test_pagination_default_page_size(self):
        """Test that pagination defaults to 3 users per page."""
        # Create 5 additional users (total 6 including admin)
        for i in range(5):
            User.objects.create_user(
                email=f'test{i}@example.com',
                password='Password123',
                username=f'testuser{i}'
            )

        res = self.client.get(USERS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 3)  # Default page size
        self.assertEqual(res.data['count'], 6)  # Total users
        self.assertIsNone(res.data['previous'])
        self.assertIsNotNone(res.data['next'])  # Should have next page

    def test_pagination_page_size_parameter(self):
        """Test that page size can be customized via query parameter."""
        # Create 5 additional users (total 6 including admin)
        for i in range(5):
            User.objects.create_user(
                email=f'test{i}@example.com',
                password='Password123',
                username=f'testuser{i}'
            )

        res = self.client.get(USERS_URL, {'size': 5})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 5)  # Custom page size
        self.assertEqual(res.data['count'], 6)  # Total users
        self.assertIsNone(res.data['previous'])
        self.assertIsNotNone(res.data['next'])  # Should have next page

    def test_pagination_page_parameter(self):
        """Test that pagination works with page parameter."""
        # Create 5 additional users (total 6 including admin)
        for i in range(5):
            User.objects.create_user(
                email=f'test{i}@example.com',
                password='Password123',
                username=f'testuser{i}'
            )

        # Get first page
        res_page1 = self.client.get(USERS_URL, {'size': 3})
        self.assertEqual(res_page1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_page1.data['results']), 3)
        self.assertIsNone(res_page1.data['previous'])
        self.assertIsNotNone(res_page1.data['next'])

        # Get second page
        res_page2 = self.client.get(USERS_URL, {'size': 3, 'page': 2})
        self.assertEqual(res_page2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_page2.data['results']), 3)
        self.assertIsNotNone(res_page2.data['previous'])
        self.assertIsNone(res_page2.data['next'])

    def test_pagination_max_page_size_limit(self):
        """Test that page size is limited to maximum allowed value."""
        # Create 10 additional users (total 11 including admin)
        for i in range(10):
            User.objects.create_user(
                email=f'test{i}@example.com',
                password='Password123',
                username=f'testuser{i}'
            )

        res = self.client.get(USERS_URL, {'size': 1000})  # Very large size

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should be limited to max_page_size (default 100)
        self.assertLessEqual(len(res.data['results']), 100)
        self.assertEqual(res.data['count'], 11)  # Total users
        self.assertIsNone(res.data['previous'])
        self.assertIsNone(res.data['next'])  # All users on one page

    def test_retrieve_specific_user_detail_success(self):
        """Test retrieving a specific user's details for admin."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='Password123',
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
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user.id).exists())

    def test_delete_user_with_image_success(self):
        """Test deleting a user with an image for admin."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='Password123',
            username='testuser2'
        )
        # Use an existing image file
        image_path = os.path.join(
            settings.MEDIA_ROOT, 'uploads', 'user', '45-png.png'
        )
        with open(image_path, 'rb') as image_file:
            user.image.save('45-png.png', image_file, save=True)

        self.assertTrue(os.path.exists(user.image.path))
        image_path_to_check = user.image.path

        url = reverse('user:user-detail', args=[user.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user.id).exists())
        self.assertFalse(os.path.exists(image_path_to_check))

    def test_update_user_success(self):
        """Test updating a user for admin."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        payload = {'username': 'newusername'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, payload['username'])

    def test_partial_update_user_without_password_success(self):
        """Test partial update of user details without providing
        password fields."""
        user = User.objects.create_user(
            email='test_partial@example.com',
            password='Password123',
            username='testuser_partial'
        )
        url = reverse('user:user-detail', args=[user.id])

        # Update username without providing password fields
        # (should work with partial=True)
        payload = {'username': 'updated_username'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, 'updated_username')
        # Verify password remains unchanged
        self.assertTrue(user.check_password('Password123'))

    def test_partial_update_user_with_password_success(self):
        """Test partial update of user details with password
        fields provided."""
        user = User.objects.create_user(
            email='test_password@example.com',
            password='Oldpassword123',
            username='testuser_password'
        )
        url = reverse('user:user-detail', args=[user.id])

        # Update password with both password and passwordRepeat fields
        payload = {
            'password': 'Newpassword123',
            'passwordRepeat': 'Newpassword123'
        }
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        # Verify password was updated
        self.assertTrue(user.check_password('Newpassword123'))


class StaffUserApiTests(TestCase):
    """Test the staff features of the user API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='staff@example.com',
            password='Password123',
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
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_for_staff_fail(self):
        """Test deleting a user for staff fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_for_staff_fail(self):
        """Test updating a user for staff fails."""
        user = User.objects.create_user(
            email='test2@example.com',
            password='Password123',
            username='testuser2'
        )
        url = reverse('user:user-detail', args=[user.id])
        payload = {'username': 'newusername'}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_blacklists_refresh_token(self):
        """Test that logging out blacklists the refresh token.
        (Core token blacklisting verification)"""
        refresh = RefreshToken.for_user(self.user)

        payload = {'refresh': str(refresh)}
        res = self.client.post(LOGOUT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        is_blacklisted = BlacklistedToken.objects.filter(
            token__token=str(refresh)
        ).exists()
        self.assertTrue(is_blacklisted)

    def test_login_and_logout_success(self):
        """Test that a user can login and logout successfully.
        (End-to-end authentication workflow test)"""
        # Login to get refresh token
        login_res = self.client.post(TOKEN_URL, {
            'email': self.user.email,
            'password': 'Password123',
        })
        refresh_token = login_res.data['refresh']

        # Logout with the obtained refresh token
        logout_res = self.client.post(LOGOUT_URL, {'refresh': refresh_token})

        self.assertEqual(logout_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__token=refresh_token
            ).exists()
        )

    def test_logout_with_invalid_token(self):
        """Test that logging out with an invalid token returns an error."""
        payload = {'refresh': 'invalid_token'}
        res = self.client.post(LOGOUT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_refresh_token(self):
        """Test that logging out requires a refresh token."""
        res = self.client.post(LOGOUT_URL, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
