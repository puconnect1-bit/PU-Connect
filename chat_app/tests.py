from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import PushSubscription
from .utils import send_web_push

class PushNotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_get_vapid_public_key(self):
        url = reverse('chat:get_vapid_public_key')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('public_key', data)
        self.assertEqual(data['public_key'], 'BGHIEjVoT9i6fafhvoN0RhQtG8O5Om8jneGhVzOX4wEsAC6-FeYOFKYUu8mLhBIf3VhVo-X6lzmUPopv3xNNkLk')

    def test_save_push_subscription(self):
        url = reverse('chat:save_push_subscription')
        payload = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/some-token',
            'auth': 'auth_secret',
            'p256dh': 'p256dh_key'
        }
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # Verify it was stored in db
        sub = PushSubscription.objects.get(user=self.user)
        self.assertEqual(sub.endpoint, payload['endpoint'])
        self.assertEqual(sub.auth, payload['auth'])
        self.assertEqual(sub.p256dh, payload['p256dh'])

    @patch('chat_app.utils.webpush')
    def test_send_web_push(self, mock_webpush):
        # Create a subscription for the user
        sub = PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/some-token',
            auth='auth_secret',
            p256dh='p256dh_key'
        )
        
        send_web_push(self.user, 'Test Title', 'Test Message', '/some-link/')
        
        # Verify webpush was called once
        mock_webpush.assert_called_once()
        args, kwargs = mock_webpush.call_args
        self.assertEqual(kwargs['subscription_info']['endpoint'], sub.endpoint)
        self.assertEqual(kwargs['subscription_info']['keys']['auth'], sub.auth)
        self.assertEqual(kwargs['subscription_info']['keys']['p256dh'], sub.p256dh)
        
        # Verify payload contains title and message
        import json
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['title'], 'Test Title')
        self.assertEqual(payload['body'], 'Test Message')
        self.assertEqual(payload['data']['url'], '/some-link/')
