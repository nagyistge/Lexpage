from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.lorem_ipsum import words
from notifications.models import Notification
from rest_framework.test import APITestCase


class NotificationTests(APITestCase):
    fixtures = ['devel']

    def test_dismiss_notification_logged_out(self):
        """A logged out user can not dismiss a notification"""
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 1)
        response = self.client.delete(reverse('notification_api_dismiss', kwargs={'pk': notifications[0].id}))
        self.assertEqual(response.status_code, 403)
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 1)

    def test_dismiss_notification_logged_in(self):
        self.client.login(username='user1', password='user1')
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 1)
        notification_id = notifications[0].id
        response = self.client.delete(reverse('notification_api_dismiss', kwargs={'pk': notification_id}))
        self.assertEqual(response.status_code, 204)
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 0)
        response = self.client.delete(reverse('notification_api_dismiss', kwargs={'pk': notification_id}))
        self.assertEqual(response.status_code, 404)

    def test_dismiss_notification_other_user(self):
        User.objects.create_user(
            username='user2', email='user2@example.com', password='top_secret')
        self.client.login(username='user2', password='top_secret')
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 1)
        response = self.client.delete(reverse('notification_api_dismiss', kwargs={'pk': notifications[0].id}))
        self.assertEqual(response.status_code, 404)
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 1)

    def test_dismiss_notification_by_showing(self):
        self.client.login(username='user1', password='user1')
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 1)
        notification_id = notifications[0].id
        response = self.client.get(reverse('notification_show', kwargs={'pk': notification_id}))
        self.assertEqual(response.status_code, 302)
        notifications = Notification.objects.filter(recipient=User.objects.get(username='user1'))
        self.assertEqual(len(notifications), 0)

    def test_list_notification_logged_out(self):
        """A logged out user can not list notifications"""
        response = self.client.get(reverse('notifications_api_list'), format='json')
        self.assertEqual(response.status_code, 403)

    def test_list_notification_logged_in(self):
        """A logged in user can list notifications"""
        Notification.objects.all().delete()

        self.client.login(username='user1', password='user1')
        user = User.objects.get(username='user1')

        Notification(recipient=user, app='test', key='1').save()
        Notification(recipient=user, app='test', key='2').save()
        Notification(recipient=user, app='test', key='3').save()

        response = self.client.get(reverse('notifications_api_list'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)

    def test_manager(self):
        notification = {
            'title': words(2, False),
            'description': words(6, False),
            'recipient': User.objects.get(username='user1'),
            'app': 'game',
            'key': 'bar',
        }
        _, created = Notification.objects.get_or_create(**notification)
        self.assertTrue(created)

        _, created = Notification.objects.get_or_create(**notification)
        self.assertFalse(created)


class NotificationCachingTests(APITestCase):
    def setUp(self):
        cache.clear()

        self.url = reverse('notifications_api_list')

        # Log in
        self.user = User.objects.create_user(username='user1', email='user1@example.com', password='user1')
        self.client.login(username='user1', password='user1')

        # First response should return an hash
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.last_hash = response.data['hash']

    def test_missing_hash(self):
        """
        A request with a missing hash should lead to a 200 with the same hash.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.last_hash, response.data['hash'])

    def test_invalid_hash(self):
        """
        A request with an invalid hash should lead to a 200 with the same hash.
        """
        response = self.client.get(self.url + '?hash=blablabla')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.last_hash, response.data['hash'])

    def test_valid_hash(self):
        """
        A request with a valid existing hash should lead to a 304.
        """
        response = self.client.get(self.url + '?hash=' + self.last_hash)
        self.assertEqual(response.status_code, 304)

    def test_etag_renewal(self):
        """
        An hash should be invalidated if a new notification is posted, or edited, or deleted.
        """
        # After new notification
        notification, _ = Notification.objects.get_or_create(recipient=self.user, app='test', key='1', title='Hello World')
        response = self.client.get(self.url + '?hash=' + self.last_hash)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.last_hash, response.data['hash'])
        last_hash = response.data['hash']

        # After modification
        notification.title = 'Hello universe'
        notification.save()
        response = self.client.get(self.url + '?hash=' + self.last_hash)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.last_hash, response.data['hash'])
        self.assertNotEqual(last_hash, response.data['hash'])
        last_hash = response.data['hash']

        # After deletion
        notification.delete()
        response = self.client.get(self.url + '?hash=' + self.last_hash)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.last_hash, response.data['hash'])
        self.assertNotEqual(last_hash, response.data['hash'])
