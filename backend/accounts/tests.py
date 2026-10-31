from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from institutions.models import Institution
from audit.models import AuditLog

User = get_user_model()

class AuthenticationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            name="VJTI Mumbai",
            aicte_id="1-109724121",
            state="Maharashtra",
            email="principal@vjti.ac.in",
            phone="+91-22-24198101",
            address="Matunga, Mumbai"
        )
        self.user = User.objects.create_user(
            username="principal@vjti.ac.in",
            email="principal@vjti.ac.in",
            password="SecurFlow@2026",
            role=User.Role.INSTITUTION,
            institution=self.institution
        )

    def test_jwt_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'principal@vjti.ac.in',
            'password': 'SecurFlow@2026'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'INSTITUTION')
        self.assertEqual(response.data['user']['institution']['aicte_id'], '1-109724121')

        # Check Audit Log written on login
        login_log = AuditLog.objects.filter(actor=self.user, action=AuditLog.Action.LOGIN).first()
        self.assertIsNotNone(login_log)

    def test_jwt_login_invalid_credentials(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'principal@vjti.ac.in',
            'password': 'WrongPassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_get_current_user_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['username'], 'principal@vjti.ac.in')

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/change-password/', {
            'old_password': 'SecurFlow@2026',
            'new_password': 'NewSecurFlowPassword@2026'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        # Verify new password works
        self.client.logout()
        login_response = self.client.post('/api/auth/login/', {
            'username': 'principal@vjti.ac.in',
            'password': 'NewSecurFlowPassword@2026'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_logout_creates_audit_log(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logout_log = AuditLog.objects.filter(actor=self.user, action=AuditLog.Action.LOGOUT).first()
        self.assertIsNotNone(logout_log)
