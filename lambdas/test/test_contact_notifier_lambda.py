import unittest
from unittest.mock import patch, MagicMock
import json
from lambdas.src.contact_notifier_lambda import lambda_handler

class TestContactNotifierLambda(unittest.TestCase):

    @patch('lambdas.src.contact_notifier_lambda.boto3.client')
    def test_lambda_handler_success(self, mock_boto_client):
        # Mock the SES and SQS clients
        mock_ses = MagicMock()
        mock_sqs = MagicMock()
        mock_boto_client.side_effect = lambda service: mock_ses if service == 'ses' else mock_sqs

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
        self.assertEqual(response['body'], 'Email sent successfully')
        mock_ses.send_email.assert_called_once()
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl='mock_queue_url',
            ReceiptHandle='abc123'
        )

    @patch('lambdas.src.contact_notifier_lambda.boto3.client')
    def test_lambda_handler_missing_contact_message(self, mock_boto_client):
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

if __name__ == '__main__':
    unittest.main()
