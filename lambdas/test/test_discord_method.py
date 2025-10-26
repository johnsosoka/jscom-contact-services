import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/contact-notifier/app'))

from notification_methods import DiscordNotificationMethod


class TestDiscordNotificationMethod(unittest.TestCase):

    def setUp(self):
        """Set up environment variables for tests."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_ENABLED'] = 'true'

    def tearDown(self):
        """Clean up environment variables after tests."""
        if 'DISCORD_WEBHOOK_URL' in os.environ:
            del os.environ['DISCORD_WEBHOOK_URL']
        if 'DISCORD_ENABLED' in os.environ:
            del os.environ['DISCORD_ENABLED']

    def test_is_enabled_when_enabled(self):
        """Test that is_enabled returns True when Discord is enabled."""
        discord_method = DiscordNotificationMethod()
        self.assertTrue(discord_method.is_enabled())

    def test_is_enabled_when_disabled(self):
        """Test that is_enabled returns False when Discord is disabled."""
        os.environ['DISCORD_ENABLED'] = 'false'
        discord_method = DiscordNotificationMethod()
        self.assertFalse(discord_method.is_enabled())

    def test_is_enabled_when_no_webhook_url(self):
        """Test that is_enabled returns False when webhook URL is missing."""
        del os.environ['DISCORD_WEBHOOK_URL']
        discord_method = DiscordNotificationMethod()
        self.assertFalse(discord_method.is_enabled())

    def test_get_method_name(self):
        """Test that get_method_name returns 'discord'."""
        discord_method = DiscordNotificationMethod()
        self.assertEqual(discord_method.get_method_name(), 'discord')

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_standard_contact(self, mock_post):
        """Test sending standard contact notification to Discord."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        discord_method = DiscordNotificationMethod()

        contact_data = {
            'contact_name': 'John Doe',
            'contact_email': 'john.doe@example.com',
            'contact_message': 'This is a test message',
            'user_agent': 'Mozilla/5.0',
            'ip_address': '192.168.1.1',
            'contact_type': 'standard'
        }

        result = discord_method.send_notification(contact_data)

        # Assertions
        self.assertTrue(result['success'])
        self.assertIn('Discord notification sent successfully', result['message'])
        self.assertEqual(result['status_code'], 204)
        mock_post.assert_called_once()

        # Verify the message content
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'https://discord.com/api/webhooks/test')
        self.assertIn('John Doe', call_args[1]['data'])
        self.assertIn('john.doe@example.com', call_args[1]['data'])
        self.assertIn('This is a test message', call_args[1]['data'])

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_consulting_contact(self, mock_post):
        """Test sending consulting contact notification to Discord."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        discord_method = DiscordNotificationMethod()

        contact_data = {
            'contact_name': 'Jane Smith',
            'contact_email': 'jane@company.com',
            'contact_message': 'Interested in consulting services',
            'user_agent': 'Mozilla/5.0',
            'ip_address': '192.168.1.2',
            'contact_type': 'consulting',
            'company_name': 'Acme Corp',
            'industry': 'Technology'
        }

        result = discord_method.send_notification(contact_data)

        # Assertions
        self.assertTrue(result['success'])
        self.assertIn('Discord notification sent successfully', result['message'])
        self.assertEqual(result['status_code'], 204)
        mock_post.assert_called_once()

        # Verify the message content includes consulting fields
        call_args = mock_post.call_args
        self.assertIn('Jane Smith', call_args[1]['data'])
        self.assertIn('jane@company.com', call_args[1]['data'])
        self.assertIn('Acme Corp', call_args[1]['data'])
        self.assertIn('Technology', call_args[1]['data'])
        self.assertIn('Interested in consulting services', call_args[1]['data'])

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_request_failure(self, mock_post):
        """Test handling of request failure when sending to Discord."""
        # Mock failed response
        mock_post.side_effect = Exception('Connection error')

        discord_method = DiscordNotificationMethod()

        contact_data = {
            'contact_name': 'John Doe',
            'contact_email': 'john.doe@example.com',
            'contact_message': 'This is a test message',
            'user_agent': 'Mozilla/5.0',
            'ip_address': '192.168.1.1',
            'contact_type': 'standard'
        }

        result = discord_method.send_notification(contact_data)

        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Connection error', result['error'])

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_with_missing_optional_fields(self, mock_post):
        """Test sending notification with minimal required fields."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        discord_method = DiscordNotificationMethod()

        # Minimal contact data
        contact_data = {
            'contact_message': 'This is a test message'
        }

        result = discord_method.send_notification(contact_data)

        # Assertions
        self.assertTrue(result['success'])
        mock_post.assert_called_once()

        # Verify defaults are used
        call_args = mock_post.call_args
        self.assertIn('Unknown', call_args[1]['data'])

    def test_format_standard_message(self):
        """Test standard message formatting."""
        discord_method = DiscordNotificationMethod()

        message = discord_method._format_standard_message(
            'John Doe',
            'john.doe@example.com',
            'Test message',
            'Mozilla/5.0',
            '192.168.1.1'
        )

        # Verify message format
        self.assertIn('**New Contact Message!**', message)
        self.assertIn('John Doe', message)
        self.assertIn('john.doe@example.com', message)
        self.assertIn('Test message', message)
        self.assertIn('Mozilla/5.0', message)
        self.assertIn('192.168.1.1', message)
        self.assertIn('John Has Been Contacted.', message)

    def test_format_consulting_message(self):
        """Test consulting message formatting."""
        discord_method = DiscordNotificationMethod()

        message = discord_method._format_consulting_message(
            'Jane Smith',
            'jane@company.com',
            'Consulting inquiry',
            'Mozilla/5.0',
            '192.168.1.2',
            'Acme Corp',
            'Technology'
        )

        # Verify message format
        self.assertIn('**New Consulting Contact Message!**', message)
        self.assertIn('Jane Smith', message)
        self.assertIn('jane@company.com', message)
        self.assertIn('Consulting inquiry', message)
        self.assertIn('Acme Corp', message)
        self.assertIn('Technology', message)
        self.assertIn('Mozilla/5.0', message)
        self.assertIn('192.168.1.2', message)
        self.assertIn('John Has Been Consulted!', message)

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_homelab_alert_ip_change(self, mock_post):
        """Test sending homelab IP change alert to Discord."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        discord_method = DiscordNotificationMethod()

        alert_data = {
            'contact_type': 'homelab-alert',
            'alert_type': 'ip-change',
            'contact_message': 'External IP changed: 1.2.3.4 → 5.6.7.8',
            'ip_address': '5.6.7.8',
            'previous_ip': '1.2.3.4',
            'timestamp': '2025-10-25T10:30:00Z',
            'source': 'homelab-ip-monitor'
        }

        result = discord_method.send_notification(alert_data)

        # Assertions
        self.assertTrue(result['success'])
        self.assertIn('Discord notification sent successfully', result['message'])
        mock_post.assert_called_once()

        # Verify message content
        call_args = mock_post.call_args
        message_data = json.loads(call_args[1]['data'])
        message_content = message_data['content']
        self.assertIn('🏠', message_content)
        self.assertIn('Homelab Alert: Ip Change', message_content)
        self.assertIn('External IP changed', message_content)
        self.assertIn('5.6.7.8', message_content)
        self.assertIn('1.2.3.4', message_content)
        self.assertIn('homelab-ip-monitor', message_content)

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_homelab_alert_dns_update(self, mock_post):
        """Test sending homelab DNS update alert to Discord."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        discord_method = DiscordNotificationMethod()

        alert_data = {
            'contact_type': 'homelab-alert',
            'alert_type': 'dns-update',
            'contact_message': 'DNS updated: minecraft.johnsosoka.com → 5.6.7.8',
            'domain': 'minecraft.johnsosoka.com',
            'ip_address': '5.6.7.8',
            'timestamp': '2025-10-25T10:30:00Z',
            'source': 'homelab-dns-update'
        }

        result = discord_method.send_notification(alert_data)

        # Assertions
        self.assertTrue(result['success'])
        mock_post.assert_called_once()

        # Verify message content
        call_args = mock_post.call_args
        message_data = json.loads(call_args[1]['data'])
        message_content = message_data['content']
        self.assertIn('🏠', message_content)
        self.assertIn('Homelab Alert: Dns Update', message_content)
        self.assertIn('minecraft.johnsosoka.com', message_content)
        self.assertIn('5.6.7.8', message_content)

    def test_format_homelab_alert(self):
        """Test homelab alert message formatting."""
        discord_method = DiscordNotificationMethod()

        alert_data = {
            'alert_type': 'ip-change',
            'contact_message': 'External IP changed',
            'ip_address': '5.6.7.8',
            'previous_ip': '1.2.3.4',
            'timestamp': '2025-10-25T10:30:00Z',
            'source': 'homelab-ip-monitor'
        }

        message = discord_method._format_homelab_alert(alert_data)

        # Verify message format
        self.assertIn('🏠', message)
        self.assertIn('Homelab Alert: Ip Change', message)
        self.assertIn('External IP changed', message)
        self.assertIn('**IP Address:** 5.6.7.8', message)
        self.assertIn('**Previous IP:** 1.2.3.4', message)
        self.assertIn('**Source:** homelab-ip-monitor', message)
        self.assertIn('**Timestamp:** 2025-10-25T10:30:00Z', message)

    @patch('notification_methods.discord_method.requests.post')
    def test_send_notification_unknown_type_fallback(self, mock_post):
        """Test generic fallback for unknown contact types."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        discord_method = DiscordNotificationMethod()

        unknown_data = {
            'contact_type': 'future-alert-type',
            'contact_message': 'Some future notification',
            'custom_field': 'custom_value'
        }

        result = discord_method.send_notification(unknown_data)

        # Assertions
        self.assertTrue(result['success'])
        mock_post.assert_called_once()

        # Verify generic formatting was used
        call_args = mock_post.call_args
        message_data = json.loads(call_args[1]['data'])
        message_content = message_data['content']
        self.assertIn('New Notification: Future Alert Type', message_content)
        self.assertIn('Some future notification', message_content)
        self.assertIn('Custom Field', message_content)

    def test_format_generic_message(self):
        """Test generic message formatting for unknown types."""
        discord_method = DiscordNotificationMethod()

        generic_data = {
            'contact_type': 'unknown-type',
            'contact_message': 'Generic message',
            'field1': 'value1',
            'field2': 'value2'
        }

        message = discord_method._format_generic_message(generic_data)

        # Verify message format
        self.assertIn('New Notification: Unknown Type', message)
        self.assertIn('Generic message', message)
        self.assertIn('Field1', message)
        self.assertIn('value1', message)
        self.assertIn('Field2', message)
        self.assertIn('value2', message)


if __name__ == '__main__':
    unittest.main()
