"""
Test suite for authentication endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthenticationTestCase(TestCase):
    """Test authentication endpoints."""
    
    def setUp(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_user_registration(self):
        """Test user registration."""
        response = self.client.post(
            '/api/auth/register/',
            self.user_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_user_registration_duplicate_username(self):
        """Test registration with duplicate username."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(
            '/api/auth/register/',
            self.user_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """Test user login."""
        User.objects.create_user(**self.user_data)
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(
            '/api/auth/login/',
            login_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        User.objects.create_user(**self.user_data)
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(
            '/api/auth/login/',
            login_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_profile(self):
        """Test get user profile."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_change_password(self):
        """Test change password."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        change_data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = self.client.post(
            '/api/auth/change-password/',
            change_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))
    
    def test_change_password_wrong_old_password(self):
        """Test change password with wrong old password."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        change_data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123'
        }
        response = self.client.post(
            '/api/auth/change-password/',
            change_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_request(self):
        """Test password reset request."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(
            '/api/auth/password-reset/',
            {'email': 'test@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('uid', response.data)
        self.assertIn('token', response.data)
    
    def test_password_reset_nonexistent_email(self):
        """Test password reset with non-existent email."""
        response = self.client.post(
            '/api/auth/password-reset/',
            {'email': 'nonexistent@example.com'},
            format='json'
        )
        # Should return 200 for security (don't reveal if email exists)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
