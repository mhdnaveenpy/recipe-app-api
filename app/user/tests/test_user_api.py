"""
TEST FOR THE USER API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
URL_ME = reverse('user:me')


def create_user(**kwargs):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**kwargs)

class PublicUserApiTests(TestCase):
    """Test the public feature of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test createting the user is successful"""

        payload = {
            'email': 'test@example.com',
            'password': 'Zaq!2wsx',
            'name': 'Test Name',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])

        self.assertTrue(user.check_password(payload['password']))

        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""

        payload = {
            'email': 'test@example.com',
            'password': 'Zaq!2wsx',
            'name': 'Test Name',
        }

        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passoword_too_short(self):
        """Test an error is returned if passoword is too short."""

        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test Name',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token forvalid credentials."""

        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'test-user_password1234',
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_create_token_bad_credentials(self):

        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'goodpass',
        }

        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': 'badpass',
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):

        payload = {
            'email': "test@example.com",
            'password': '',
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):

        res = self.client.get(URL_ME)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTest(TestCase):

    def setUp(self):

        self.user = create_user(
            email="test@example.com",
            password="password",
            name="Test User"
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_profile_success(self):

        res = self.client.get(URL_ME)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):

        res = self.client.post(URL_ME, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_me_successful(self):

        payload = {'name': 'TEST USER CHANGED', 'password': 'password_changed'}

        res = self.client.patch(URL_ME, payload)

        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))