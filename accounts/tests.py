import re
from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import EmailOTP, User


def _extract_code(message_body):
    return re.search(r'\b(\d{6})\b', message_body).group(1)


class LoginOTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='alice', password='s3cret-pass', email='alice@example.com',
        )

    def test_login_with_email_requires_otp_before_session_established(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'alice', 'password': 's3cret-pass',
        })
        self.assertRedirects(response, reverse('accounts:verify_otp'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertEqual(len(mail.outbox), 1)

    def test_correct_code_logs_user_in(self):
        self.client.post(reverse('accounts:login'), {
            'username': 'alice', 'password': 's3cret-pass',
        })
        code = _extract_code(mail.outbox[0].body)
        response = self.client.post(reverse('accounts:verify_otp'), {'code': code})
        self.assertRedirects(response, reverse('dashboard:redirect'), fetch_redirect_response=False)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_wrong_code_is_rejected_and_counts_attempt(self):
        self.client.post(reverse('accounts:login'), {
            'username': 'alice', 'password': 's3cret-pass',
        })
        response = self.client.post(reverse('accounts:verify_otp'), {'code': '000000'})
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        otp = EmailOTP.objects.get(user=self.user)
        self.assertEqual(otp.attempts, 1)
        self.assertFalse(otp.is_used)

    def test_expired_code_is_rejected(self):
        self.client.post(reverse('accounts:login'), {
            'username': 'alice', 'password': 's3cret-pass',
        })
        code = _extract_code(mail.outbox[0].body)
        EmailOTP.objects.filter(user=self.user).update(
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        response = self.client.post(reverse('accounts:verify_otp'), {'code': code})
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_resend_respects_cooldown_and_invalidates_previous_code(self):
        self.client.post(reverse('accounts:login'), {
            'username': 'alice', 'password': 's3cret-pass',
        })
        first_code = _extract_code(mail.outbox[0].body)
        self.client.post(reverse('accounts:resend_otp'))
        self.assertEqual(len(mail.outbox), 1, 'resend within cooldown should not send another email')

        EmailOTP.objects.filter(user=self.user).update(
            created_at=timezone.now() - timedelta(seconds=60),
        )
        self.client.post(reverse('accounts:resend_otp'))
        self.assertEqual(len(mail.outbox), 2)

        response = self.client.post(reverse('accounts:verify_otp'), {'code': first_code})
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_blank_email_account_skips_otp(self):
        User.objects.create_user(username='bob', password='s3cret-pass', email='')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'bob', 'password': 's3cret-pass',
        })
        self.assertRedirects(response, reverse('dashboard:redirect'), fetch_redirect_response=False)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_otp_without_pending_session_redirects_to_login(self):
        response = self.client.get(reverse('accounts:verify_otp'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_registration_with_email_requires_otp(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'carol', 'email': 'carol@example.com', 'phone': '',
            'password1': 'Str0ng-Passw0rd!', 'password2': 'Str0ng-Passw0rd!',
            'province': 'Kigali', 'district': 'Gasabo', 'sector': 'Kimironko',
            'cell': 'Kibagabaga', 'village': '', 'postal_address': '00000',
        })
        self.assertRedirects(response, reverse('accounts:verify_otp'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
