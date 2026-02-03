"""Tests for authentication API endpoints.

Tests user registration, login, logout, password change, and password reset.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthAPITestCase(TestCase):
    """Base test case for authentication tests."""
    
    def setUp(self):
        """Set up test client and test user."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            phone='01712345678',
            first_name='Test',
            last_name='User',
            password='Test@123456'
        )


class RegistrationTest(AuthAPITestCase):
    """Test user registration."""
    
    def test_register_user(self):
        """Test successful user registration."""
        url = '/api/v1/auth/register/'
        data = {
            'email': 'newuser@example.com',
            'phone': '01798765432',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
    
    def test_register_duplicate_email(self):
        """Test registration with existing email."""
        url = '/api/v1/auth/register/'
        data = {
            'email': 'test@example.com',  # Already exists
            'phone': '01798765432',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewPass@123',
            'password2': 'NewPass@123',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords."""
        url = '/api/v1/auth/register/'
        data = {
            'email': 'newuser@example.com',
            'phone': '01798765432',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'NewPass@123',
            'password2': 'DifferentPass@123',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTest(AuthAPITestCase):
    """Test user login."""
    
    def test_login_success(self):
        """Test successful login."""
        url = '/api/v1/auth/login/'
        data = {
            'email': 'test@example.com',
            'password': 'Test@123456',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = '/api/v1/auth/login/'
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordChangeTest(AuthAPITestCase):
    """Test password change."""
    
    def test_change_password(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/v1/auth/change-password/'
        data = {
            'old_password': 'Test@123456',
            'new_password': 'NewTest@123456',
            'new_password2': 'NewTest@123456',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewTest@123456'))
    
    def test_change_password_wrong_old(self):
        """Test password change with wrong old password."""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/v1/auth/change-password/'
        data = {
            'old_password': 'WrongOldPassword',
            'new_password': 'NewTest@123456',
            'new_password2': 'NewTest@123456',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTest(AuthAPITestCase):
    """Test password reset flow."""
    
    def test_password_reset_request(self):
        """Test password reset request."""
        url = '/api/v1/auth/password-reset/'
        data = {
            'email': 'test@example.com',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        # Development mode returns token
        self.assertIn('dev_token', response.data)
        self.assertIn('dev_uid', response.data)
    
    def test_password_reset_invalid_email(self):
        """Test password reset with invalid email."""
        url = '/api/v1/auth/password-reset/'
        data = {
            'email': 'nonexistent@example.com',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
