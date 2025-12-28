"""
Integration tests for contact-listener Lambda with Turnstile validation
"""

import json
import os
import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Set environment variable before importing Lambda module
os.environ['CONTACT_MESSAGE_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src" / "contact-listener"
sys.path.insert(0, str(src_path))

from app.contact_listener_lambda import lambda_handler


@pytest.fixture
def base_event():
    """Base API Gateway v2 event structure"""
    return {
        'isBase64Encoded': False,
        'requestContext': {
            'http': {
                'sourceIp': '192.168.1.100',
                'userAgent': 'Mozilla/5.0'
            }
        }
    }


@pytest.fixture
def mock_env():
    """Mock environment variables"""
    return {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'}


class TestTurnstileIntegration:
    """Test Turnstile validation in contact listener"""

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_successful_submission_with_valid_turnstile(self, mock_validate, mock_sqs, base_event):
        """Test successful contact submission with valid Turnstile token"""
        # Mock Turnstile validation success
        mock_validate.return_value = True

        # Mock SQS response
        mock_sqs.send_message.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }

        # Create event with valid payload
        base_event['body'] = json.dumps({
            'turnstile_token': 'valid-token',
            'turnstile_site': 'sosoka.com',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message',
            'contact_name': 'Test User'
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 200
        assert 'Message Received' in json.loads(response['body'])['message']
        mock_validate.assert_called_once_with('valid-token', '192.168.1.100', 'sosoka.com')
        mock_sqs.send_message.assert_called_once()

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_missing_turnstile_token(self, mock_validate, mock_sqs, base_event):
        """Test rejection when Turnstile token is missing"""
        # Create event without Turnstile token
        base_event['body'] = json.dumps({
            'contact_email': 'test@example.com',
            'contact_message': 'Test message',
            'contact_name': 'Test User'
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 403
        assert json.loads(response['body'])['error'] == 'Security verification required'
        mock_validate.assert_not_called()
        mock_sqs.send_message.assert_not_called()

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_invalid_turnstile_token(self, mock_validate, mock_sqs, base_event):
        """Test rejection when Turnstile validation fails"""
        # Mock Turnstile validation failure
        mock_validate.return_value = False

        # Create event with invalid token
        base_event['body'] = json.dumps({
            'turnstile_token': 'invalid-token',
            'turnstile_site': 'sosoka.com',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message',
            'contact_name': 'Test User'
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 403
        assert json.loads(response['body'])['error'] == 'Security verification failed'
        mock_validate.assert_called_once_with('invalid-token', '192.168.1.100', 'sosoka.com')
        mock_sqs.send_message.assert_not_called()

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_johnsosoka_com_site(self, mock_validate, mock_sqs, base_event):
        """Test validation with johnsosoka.com site"""
        # Mock Turnstile validation success
        mock_validate.return_value = True

        # Mock SQS response
        mock_sqs.send_message.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }

        # Create event with johnsosoka.com site
        base_event['body'] = json.dumps({
            'turnstile_token': 'valid-token',
            'turnstile_site': 'johnsosoka.com',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message',
            'contact_name': 'Test User'
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 200
        mock_validate.assert_called_once_with('valid-token', '192.168.1.100', 'johnsosoka.com')

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_missing_turnstile_site_defaults_to_empty(self, mock_validate, mock_sqs, base_event):
        """Test missing site parameter defaults to empty string"""
        # Mock Turnstile validation failure (invalid site)
        mock_validate.return_value = False

        # Create event without site parameter
        base_event['body'] = json.dumps({
            'turnstile_token': 'valid-token',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message',
            'contact_name': 'Test User'
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 403
        mock_validate.assert_called_once_with('valid-token', '192.168.1.100', '')

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_consulting_contact_with_turnstile(self, mock_validate, mock_sqs, base_event):
        """Test consulting contact form with Turnstile validation"""
        # Mock Turnstile validation success
        mock_validate.return_value = True

        # Mock SQS response
        mock_sqs.send_message.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }

        # Create consulting contact event
        base_event['body'] = json.dumps({
            'turnstile_token': 'valid-token',
            'turnstile_site': 'sosoka.com',
            'contact_email': 'test@company.com',
            'contact_message': 'Interested in consulting',
            'contact_name': 'Test User',
            'company_name': 'Acme Corp',
            'industry': 'Technology',
            'consulting_contact': True
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 200
        mock_validate.assert_called_once_with('valid-token', '192.168.1.100', 'sosoka.com')

        # Verify SQS message contains consulting fields
        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]['MessageBody'])
        assert message_body['contact_type'] == 'consulting'
        assert message_body['company_name'] == 'Acme Corp'
        assert message_body['industry'] == 'Technology'

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_turnstile_validation_before_required_field_check(self, mock_validate, mock_sqs, base_event):
        """Test that Turnstile validation happens before required field validation"""
        # Mock Turnstile validation failure
        mock_validate.return_value = False

        # Create event with missing required field (but has Turnstile token)
        base_event['body'] = json.dumps({
            'turnstile_token': 'invalid-token',
            'turnstile_site': 'sosoka.com',
            'contact_email': 'test@example.com',
            'contact_name': 'Test User'
            # Missing contact_message
        })

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions - should fail on Turnstile first, not required field
        assert response['statusCode'] == 403
        assert json.loads(response['body'])['error'] == 'Security verification failed'
        mock_sqs.send_message.assert_not_called()

    @patch.dict(os.environ, {'CONTACT_MESSAGE_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'})
    @patch('app.contact_listener_lambda.sqs')
    @patch('app.contact_listener_lambda.validate_turnstile')
    def test_base64_encoded_body_with_turnstile(self, mock_validate, mock_sqs, base_event):
        """Test base64 encoded request body with Turnstile"""
        import base64

        # Mock Turnstile validation success
        mock_validate.return_value = True

        # Mock SQS response
        mock_sqs.send_message.return_value = {
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }

        # Create base64 encoded payload
        payload = {
            'turnstile_token': 'valid-token',
            'turnstile_site': 'sosoka.com',
            'contact_email': 'test@example.com',
            'contact_message': 'Test message',
            'contact_name': 'Test User'
        }
        encoded_body = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')

        base_event['isBase64Encoded'] = True
        base_event['body'] = encoded_body

        # Execute
        response = lambda_handler(base_event, None)

        # Assertions
        assert response['statusCode'] == 200
        mock_validate.assert_called_once_with('valid-token', '192.168.1.100', 'sosoka.com')
