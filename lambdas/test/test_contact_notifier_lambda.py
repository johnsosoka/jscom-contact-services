import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/contact-notifier/app'))

from contact_notifier_lambda import lambda_handler


class TestContactNotifierLambda(unittest.TestCase):

    def setUp(self):
        """Set up environment variables for tests."""
        os.environ['CONTACT_NOTIFY_QUEUE'] = 'mock_queue_url'
        os.environ['EMAIL_ENABLED'] = 'true'
        os.environ['EMAIL_SENDER'] = 'mail@johnsosoka.com'
        os.environ['EMAIL_RECIPIENT'] = 'im@johnsosoka.com'

    @patch('contact_notifier_lambda.EmailNotificationMethod')
    @patch('contact_notifier_lambda.boto3.client')
    def test_lambda_handler_success(self, mock_boto_client, mock_email_method_class):
        # Mock the email notification method
        mock_email_method = MagicMock()
        mock_email_method.is_enabled.return_value = True
        mock_email_method.get_method_name.return_value = 'email'
        mock_email_method.send_notification.return_value = {
            'success': True,
            'message': 'Email sent successfully'
        }
        mock_email_method_class.return_value = mock_email_method

        # Mock SQS client
        mock_sqs = MagicMock()
        mock_boto_client.return_value = mock_sqs

        # Mock the event
        event = {
            'Records': [{
                'body': json.dumps({
                    'contact_message': 'Hello, I need help!',
                    'contact_name': 'John Doe',
                    'contact_email': 'john.doe@example.com',
                    'user_agent': 'Mozilla/5.0',
                    'ip_address': '192.168.1.1',
                    'company_name': 'Example Corp',
                    'industry': 'Tech',
                    'contact_type': 'standard'
                }),
                'receiptHandle': 'abc123'
            }]
        }

        # Call the lambda_handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['message'], 'All notifications sent successfully')
        mock_email_method.send_notification.assert_called_once()
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl='mock_queue_url',
            ReceiptHandle='abc123'
        )

    @patch('contact_notifier_lambda.EmailNotificationMethod')
    def test_lambda_handler_missing_contact_message(self, mock_email_method_class):
        # Mock the email notification method
        mock_email_method = MagicMock()
        mock_email_method.is_enabled.return_value = True
        mock_email_method_class.return_value = mock_email_method

        # Mock the event with missing contact_message
        event = {
            'Records': [{
                'body': json.dumps({
                    'contact_name': 'John Doe'
                }),
                'receiptHandle': 'abc123'
            }]
        }

        # Call the lambda_handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], 'Missing required field: contact_message')

    @patch('contact_notifier_lambda.EmailNotificationMethod')
    @patch('contact_notifier_lambda.boto3.client')
    def test_lambda_handler_notification_failure(self, mock_boto_client, mock_email_method_class):
        # Mock the email notification method to fail
        mock_email_method = MagicMock()
        mock_email_method.is_enabled.return_value = True
        mock_email_method.get_method_name.return_value = 'email'
        mock_email_method.send_notification.return_value = {
            'success': False,
            'error': 'SES error'
        }
        mock_email_method_class.return_value = mock_email_method

        # Mock SQS client
        mock_sqs = MagicMock()
        mock_boto_client.return_value = mock_sqs

        # Mock the event
        event = {
            'Records': [{
                'body': json.dumps({
                    'contact_message': 'Hello, I need help!',
                    'contact_name': 'John Doe',
                    'contact_email': 'john.doe@example.com',
                    'user_agent': 'Mozilla/5.0',
                    'ip_address': '192.168.1.1',
                    'contact_type': 'standard'
                }),
                'receiptHandle': 'abc123'
            }]
        }

        # Call the lambda_handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['message'], 'One or more notification methods failed')
        # Message should NOT be deleted from queue when notification fails
        mock_sqs.delete_message.assert_not_called()

    @patch('contact_notifier_lambda.EmailNotificationMethod')
    def test_lambda_handler_no_enabled_methods(self, mock_email_method_class):
        # Mock the email notification method as disabled
        mock_email_method = MagicMock()
        mock_email_method.is_enabled.return_value = False
        mock_email_method_class.return_value = mock_email_method

        # Mock the event
        event = {
            'Records': [{
                'body': json.dumps({
                    'contact_message': 'Hello, I need help!',
                    'contact_name': 'John Doe',
                    'contact_email': 'john.doe@example.com',
                    'user_agent': 'Mozilla/5.0',
                    'ip_address': '192.168.1.1',
                    'contact_type': 'standard'
                }),
                'receiptHandle': 'abc123'
            }]
        }

        # Call the lambda_handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], 'No notification methods enabled')

if __name__ == '__main__':
    unittest.main()
