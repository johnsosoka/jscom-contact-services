"""
Comprehensive test suite for the contact-admin Lambda function.

Tests cover:
- Handler functions for messages and blocked contacts
- DynamoDB helper utilities for model conversions
- Lambda handler integration with API Gateway events
- Error handling for validation, business logic, and unexpected errors
"""

import pytest
import json
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Any

# Set environment variables before importing the module
os.environ['ALL_CONTACT_MESSAGES_TABLE_NAME'] = 'test-messages-table'
os.environ['BLOCKED_CONTACTS_TABLE_NAME'] = 'test-blocked-table'

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/contact-admin'))

# Import after environment variables are set
from app.handlers.messages import list_messages, get_message_by_id, get_stats
from app.handlers.blocked_contacts import list_blocked_contacts, block_contact, unblock_contact
from app.utils.dynamodb_helper import (
    item_to_contact_message,
    item_to_blocked_contact,
    contact_message_to_item,
    blocked_contact_to_item
)
from app.models.domain_models import ContactMessage, BlockedContact
from app.models.request_models import BlockContactRequest
from app import contact_admin_lambda


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_contact_message_dict() -> dict[str, Any]:
    """Sample ContactMessage as DynamoDB item."""
    return {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'contact_email': 'john@example.com',
        'contact_message': 'Interested in your services',
        'contact_name': 'John Doe',
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'timestamp': 1697840000,
        'is_blocked': 0,
        'contact_type': 'standard'
    }


@pytest.fixture
def sample_consulting_message_dict() -> dict[str, Any]:
    """Sample consulting ContactMessage as DynamoDB item."""
    return {
        'id': '660e8400-e29b-41d4-a716-446655440001',
        'contact_email': 'jane@company.com',
        'contact_message': 'Need consulting services',
        'contact_name': 'Jane Smith',
        'ip_address': '192.168.1.2',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'timestamp': 1697840100,
        'is_blocked': 0,
        'contact_type': 'consulting',
        'company_name': 'Acme Corp',
        'industry': 'Technology'
    }


@pytest.fixture
def sample_blocked_message_dict() -> dict[str, Any]:
    """Sample blocked ContactMessage as DynamoDB item."""
    return {
        'id': '770e8400-e29b-41d4-a716-446655440002',
        'contact_email': 'spam@example.com',
        'contact_message': 'Spam message',
        'contact_name': 'Spammer',
        'ip_address': '10.0.0.1',
        'user_agent': 'BadBot/1.0',
        'timestamp': 1697840200,
        'is_blocked': 1,
        'contact_type': 'standard'
    }


@pytest.fixture
def sample_blocked_contact_dict() -> dict[str, Any]:
    """Sample BlockedContact as DynamoDB item."""
    return {
        'id': '880e8400-e29b-41d4-a716-446655440003',
        'ip_address': '10.0.0.1',
        'user_agent': 'BadBot/1.0',
        'is_blocked': 1
    }


@pytest.fixture
def sample_contact_message() -> ContactMessage:
    """Sample ContactMessage Pydantic model."""
    return ContactMessage(
        id='550e8400-e29b-41d4-a716-446655440000',
        contact_email='john@example.com',
        contact_message='Interested in your services',
        contact_name='John Doe',
        ip_address='192.168.1.1',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        timestamp=1697840000,
        is_blocked=0,
        contact_type='standard'
    )


@pytest.fixture
def sample_blocked_contact() -> BlockedContact:
    """Sample BlockedContact Pydantic model."""
    return BlockedContact(
        id='880e8400-e29b-41d4-a716-446655440003',
        ip_address='10.0.0.1',
        user_agent='BadBot/1.0',
        is_blocked=1
    )


@pytest.fixture
def mock_dynamodb_table() -> MagicMock:
    """Mock DynamoDB Table resource."""
    return MagicMock()


# ============================================================================
# DYNAMODB HELPER TESTS
# ============================================================================

class TestDynamoDBHelpers:
    """Tests for DynamoDB conversion utilities."""

    def test_item_to_contact_message_standard(self, sample_contact_message_dict):
        """Convert standard DynamoDB item to ContactMessage."""
        result = item_to_contact_message(sample_contact_message_dict)

        assert isinstance(result, ContactMessage)
        assert result.id == '550e8400-e29b-41d4-a716-446655440000'
        assert result.contact_email == 'john@example.com'
        assert result.contact_message == 'Interested in your services'
        assert result.contact_name == 'John Doe'
        assert result.ip_address == '192.168.1.1'
        assert result.user_agent == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        assert result.timestamp == 1697840000
        assert result.is_blocked == 0
        assert result.contact_type == 'standard'
        assert result.company_name is None
        assert result.industry is None

    def test_item_to_contact_message_consulting(self, sample_consulting_message_dict):
        """Convert consulting DynamoDB item to ContactMessage with optional fields."""
        result = item_to_contact_message(sample_consulting_message_dict)

        assert isinstance(result, ContactMessage)
        assert result.contact_type == 'consulting'
        assert result.company_name == 'Acme Corp'
        assert result.industry == 'Technology'

    def test_item_to_contact_message_missing_optional_fields(self):
        """Handle missing optional fields gracefully."""
        minimal_item = {
            'id': 'test-id',
            'contact_message': 'Test message',
            'ip_address': '127.0.0.1',
            'user_agent': 'TestBot',
            'timestamp': 1697840000,
            'is_blocked': 0
        }

        result = item_to_contact_message(minimal_item)

        assert result.id == 'test-id'
        assert result.contact_email is None
        assert result.contact_name is None
        assert result.contact_type == 'standard'  # Default value
        assert result.company_name is None
        assert result.industry is None

    def test_contact_message_to_item_standard(self, sample_contact_message):
        """Convert ContactMessage Pydantic model to DynamoDB item."""
        result = contact_message_to_item(sample_contact_message)

        assert isinstance(result, dict)
        assert result['id'] == '550e8400-e29b-41d4-a716-446655440000'
        assert result['contact_email'] == 'john@example.com'
        assert result['contact_message'] == 'Interested in your services'
        assert result['contact_name'] == 'John Doe'
        assert result['ip_address'] == '192.168.1.1'
        assert result['user_agent'] == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        assert result['timestamp'] == 1697840000
        assert result['is_blocked'] == 0
        assert result['contact_type'] == 'standard'

    def test_contact_message_to_item_excludes_none_values(self):
        """Exclude None values from DynamoDB item."""
        message = ContactMessage(
            id='test-id',
            contact_message='Test',
            ip_address='127.0.0.1',
            user_agent='TestBot',
            timestamp=1697840000,
            is_blocked=0,
            contact_type='standard'
        )

        result = contact_message_to_item(message)

        assert 'contact_email' not in result
        assert 'contact_name' not in result
        assert 'company_name' not in result
        assert 'industry' not in result

    def test_item_to_blocked_contact(self, sample_blocked_contact_dict):
        """Convert DynamoDB item to BlockedContact."""
        result = item_to_blocked_contact(sample_blocked_contact_dict)

        assert isinstance(result, BlockedContact)
        assert result.id == '880e8400-e29b-41d4-a716-446655440003'
        assert result.ip_address == '10.0.0.1'
        assert result.user_agent == 'BadBot/1.0'
        assert result.is_blocked == 1

    def test_blocked_contact_to_item(self, sample_blocked_contact):
        """Convert BlockedContact Pydantic model to DynamoDB item."""
        result = blocked_contact_to_item(sample_blocked_contact)

        assert isinstance(result, dict)
        assert result['id'] == '880e8400-e29b-41d4-a716-446655440003'
        assert result['ip_address'] == '10.0.0.1'
        assert result['user_agent'] == 'BadBot/1.0'
        assert result['is_blocked'] == 1


# ============================================================================
# MESSAGE HANDLER TESTS
# ============================================================================

class TestMessageHandlers:
    """Tests for message operation handlers."""

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_success(
        self,
        mock_table,
        sample_contact_message_dict,
        sample_consulting_message_dict
    ):
        """List messages with successful pagination."""
        mock_table.scan.return_value = {
            'Items': [sample_contact_message_dict, sample_consulting_message_dict],
            'LastEvaluatedKey': {'id': 'last-key'}
        }

        result = list_messages(limit=50)

        assert result.count == 2
        assert len(result.messages) == 2
        assert result.next_token is not None
        assert result.messages[0].contact_type in ['standard', 'consulting']
        mock_table.scan.assert_called_once()

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_with_filter(
        self,
        mock_table,
        sample_consulting_message_dict
    ):
        """Filter messages by contact_type."""
        mock_table.scan.return_value = {
            'Items': [sample_consulting_message_dict],
        }

        result = list_messages(limit=50, contact_type='consulting')

        assert result.count == 1
        assert result.messages[0].contact_type == 'consulting'
        mock_table.scan.assert_called_once()
        call_kwargs = mock_table.scan.call_args[1]
        assert 'FilterExpression' in call_kwargs
        assert 'ExpressionAttributeValues' in call_kwargs

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_empty(self, mock_table):
        """Handle empty messages table."""
        mock_table.scan.return_value = {
            'Items': []
        }

        result = list_messages(limit=50)

        assert result.count == 0
        assert len(result.messages) == 0
        assert result.next_token is None

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_with_pagination_token(
        self,
        mock_table,
        sample_contact_message_dict
    ):
        """Use pagination token to retrieve next page."""
        import base64

        # Create a valid pagination token
        last_key = {'id': 'previous-id'}
        token = base64.b64encode(json.dumps(last_key).encode('utf-8')).decode('utf-8')

        mock_table.scan.return_value = {
            'Items': [sample_contact_message_dict],
        }

        result = list_messages(limit=50, next_token=token)

        assert result.count == 1
        call_kwargs = mock_table.scan.call_args[1]
        assert 'ExclusiveStartKey' in call_kwargs

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_invalid_pagination_token(self, mock_table):
        """Raise ValueError for invalid pagination token."""
        with pytest.raises(ValueError, match="Invalid pagination token"):
            list_messages(limit=50, next_token='invalid-token')

    @patch('app.handlers.messages.messages_table')
    def test_get_message_by_id_success(
        self,
        mock_table,
        sample_contact_message_dict
    ):
        """Retrieve message by valid ID."""
        mock_table.get_item.return_value = {
            'Item': sample_contact_message_dict
        }

        result = get_message_by_id('550e8400-e29b-41d4-a716-446655440000')

        assert result is not None
        assert result.id == '550e8400-e29b-41d4-a716-446655440000'
        assert result.contact_email == 'john@example.com'
        mock_table.get_item.assert_called_once_with(
            Key={'id': '550e8400-e29b-41d4-a716-446655440000'}
        )

    @patch('app.handlers.messages.messages_table')
    def test_get_message_by_id_not_found(self, mock_table):
        """Return None for non-existent message ID."""
        mock_table.get_item.return_value = {}

        result = get_message_by_id('non-existent-id')

        assert result is None

    @patch('app.handlers.messages.dynamodb')
    @patch('app.handlers.messages.messages_table')
    def test_get_stats_success(
        self,
        mock_messages_table,
        mock_dynamodb,
        sample_contact_message_dict,
        sample_consulting_message_dict,
        sample_blocked_message_dict,
        sample_blocked_contact_dict
    ):
        """Calculate system statistics correctly."""
        # Mock blocked table
        mock_blocked_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_blocked_table

        # Mock messages scan
        current_time = int(time.time())
        recent_message = sample_contact_message_dict.copy()
        recent_message['timestamp'] = current_time - 3600  # 1 hour ago

        mock_messages_table.scan.return_value = {
            'Items': [
                sample_contact_message_dict,
                sample_consulting_message_dict,
                sample_blocked_message_dict,
                recent_message
            ]
        }

        # Mock blocked contacts scan
        mock_blocked_table.scan.return_value = {
            'Items': [sample_blocked_contact_dict]
        }

        result = get_stats()

        assert result.total_messages == 4
        assert result.blocked_count == 1
        assert result.unblocked_count == 3
        assert result.total_blocked_ips == 1
        assert result.recent_messages_24h == 1
        assert result.consulting_messages == 1
        assert result.standard_messages == 3

    @patch('app.handlers.messages.dynamodb')
    @patch('app.handlers.messages.messages_table')
    def test_get_stats_empty_tables(
        self,
        mock_messages_table,
        mock_dynamodb
    ):
        """Handle empty tables gracefully."""
        mock_blocked_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_blocked_table

        mock_messages_table.scan.return_value = {'Items': []}
        mock_blocked_table.scan.return_value = {'Items': []}

        result = get_stats()

        assert result.total_messages == 0
        assert result.blocked_count == 0
        assert result.unblocked_count == 0
        assert result.total_blocked_ips == 0
        assert result.recent_messages_24h == 0
        assert result.consulting_messages == 0
        assert result.standard_messages == 0

    @patch('app.handlers.messages.dynamodb')
    @patch('app.handlers.messages.messages_table')
    def test_get_stats_with_pagination(
        self,
        mock_messages_table,
        mock_dynamodb,
        sample_contact_message_dict
    ):
        """Handle paginated results when calculating stats."""
        mock_blocked_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_blocked_table

        # Simulate pagination
        mock_messages_table.scan.side_effect = [
            {
                'Items': [sample_contact_message_dict],
                'LastEvaluatedKey': {'id': 'key1'}
            },
            {
                'Items': [sample_contact_message_dict],
            }
        ]

        mock_blocked_table.scan.return_value = {'Items': []}

        result = get_stats()

        assert result.total_messages == 2
        assert mock_messages_table.scan.call_count == 2


# ============================================================================
# BLOCKED CONTACTS HANDLER TESTS
# ============================================================================

class TestBlockedContactsHandlers:
    """Tests for blocked contacts operation handlers."""

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_list_blocked_contacts_success(
        self,
        mock_table,
        sample_blocked_contact_dict
    ):
        """List all blocked contacts."""
        mock_table.scan.return_value = {
            'Items': [sample_blocked_contact_dict]
        }

        result = list_blocked_contacts()

        assert result.count == 1
        assert len(result.blocked_contacts) == 1
        assert result.blocked_contacts[0].ip_address == '10.0.0.1'
        mock_table.scan.assert_called_once()

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_list_blocked_contacts_empty(self, mock_table):
        """Handle empty blocked contacts table."""
        mock_table.scan.return_value = {'Items': []}

        result = list_blocked_contacts()

        assert result.count == 0
        assert len(result.blocked_contacts) == 0

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_list_blocked_contacts_with_pagination(
        self,
        mock_table,
        sample_blocked_contact_dict
    ):
        """Handle paginated results."""
        mock_table.scan.side_effect = [
            {
                'Items': [sample_blocked_contact_dict],
                'LastEvaluatedKey': {'id': 'key1'}
            },
            {
                'Items': [sample_blocked_contact_dict]
            }
        ]

        result = list_blocked_contacts()

        assert result.count == 2
        assert mock_table.scan.call_count == 2

    @patch('app.handlers.blocked_contacts.blocked_table')
    @patch('app.handlers.blocked_contacts.uuid')
    def test_block_contact_success(self, mock_uuid, mock_table):
        """Add new IP to blocked list."""
        mock_uuid.uuid4.return_value = '550e8400-e29b-41d4-a716-446655440000'
        mock_table.scan.return_value = {'Items': []}

        request = BlockContactRequest(
            ip_address='192.168.1.100',
            user_agent='BadBot/1.0'
        )

        result = block_contact(request)

        assert isinstance(result, BlockedContact)
        assert result.ip_address == '192.168.1.100'
        assert result.user_agent == 'BadBot/1.0'
        assert result.is_blocked == 1
        mock_table.put_item.assert_called_once()

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_block_contact_duplicate(
        self,
        mock_table,
        sample_blocked_contact_dict
    ):
        """Raise ValueError when IP is already blocked."""
        mock_table.scan.return_value = {
            'Items': [sample_blocked_contact_dict]
        }

        request = BlockContactRequest(
            ip_address='10.0.0.1',
            user_agent='BadBot/1.0'
        )

        with pytest.raises(ValueError, match="already blocked"):
            block_contact(request)

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_unblock_contact_success(self, mock_table):
        """Remove blocked contact by ID."""
        mock_table.get_item.return_value = {
            'Item': {'id': 'test-id', 'ip_address': '10.0.0.1'}
        }

        result = unblock_contact('test-id')

        assert result is True
        mock_table.delete_item.assert_called_once_with(Key={'id': 'test-id'})

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_unblock_contact_not_found(self, mock_table):
        """Return False when blocked contact doesn't exist."""
        mock_table.get_item.return_value = {}

        result = unblock_contact('non-existent-id')

        assert result is False
        mock_table.delete_item.assert_not_called()


# ============================================================================
# LAMBDA HANDLER INTEGRATION TESTS
# ============================================================================

class TestLambdaHandlerIntegration:
    """End-to-end tests for Lambda handler with API Gateway events."""

    @patch('app.handlers.messages.messages_table')
    def test_lambda_handler_list_messages(
        self,
        mock_table,
        sample_contact_message_dict
    ):
        """Test GET /admin/messages endpoint."""
        mock_table.scan.return_value = {
            'Items': [sample_contact_message_dict]
        }

        event = {
            'resource': '/admin/messages',
            'path': '/admin/messages',
            'httpMethod': 'GET',
            'queryStringParameters': {'limit': '50'},
            'requestContext': {
                'resourcePath': '/admin/messages',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 200
        assert 'data' in body
        assert body['data']['count'] == 1

    @patch('app.handlers.messages.messages_table')
    def test_lambda_handler_get_message(
        self,
        mock_table,
        sample_contact_message_dict
    ):
        """Test GET /admin/messages/{id} endpoint."""
        message_id = '550e8400-e29b-41d4-a716-446655440000'
        mock_table.get_item.return_value = {
            'Item': sample_contact_message_dict
        }

        event = {
            'resource': '/admin/messages/{message_id}',
            'path': f'/admin/messages/{message_id}',
            'httpMethod': 'GET',
            'pathParameters': {'message_id': message_id},
            'requestContext': {
                'resourcePath': '/admin/messages/{message_id}',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 200
        assert body['data']['id'] == message_id

    @patch('app.handlers.messages.messages_table')
    def test_lambda_handler_get_message_not_found(self, mock_table):
        """Test GET /admin/messages/{id} with non-existent ID."""
        mock_table.get_item.return_value = {}

        event = {
            'resource': '/admin/messages/{message_id}',
            'path': '/admin/messages/non-existent-id',
            'httpMethod': 'GET',
            'pathParameters': {'message_id': 'non-existent-id'},
            'requestContext': {
                'resourcePath': '/admin/messages/{message_id}',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['status'] == 404
        assert 'not found' in body['error']

    @patch('app.handlers.messages.dynamodb')
    @patch('app.handlers.messages.messages_table')
    def test_lambda_handler_stats(
        self,
        mock_messages_table,
        mock_dynamodb
    ):
        """Test GET /admin/stats endpoint."""
        mock_blocked_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_blocked_table

        mock_messages_table.scan.return_value = {'Items': []}
        mock_blocked_table.scan.return_value = {'Items': []}

        event = {
            'resource': '/admin/stats',
            'path': '/admin/stats',
            'httpMethod': 'GET',
            'requestContext': {
                'resourcePath': '/admin/stats',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 200
        assert 'data' in body
        assert body['data']['total_messages'] == 0

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_lambda_handler_list_blocked(
        self,
        mock_table,
        sample_blocked_contact_dict
    ):
        """Test GET /admin/blocked endpoint."""
        mock_table.scan.return_value = {
            'Items': [sample_blocked_contact_dict]
        }

        event = {
            'resource': '/admin/blocked',
            'path': '/admin/blocked',
            'httpMethod': 'GET',
            'requestContext': {
                'resourcePath': '/admin/blocked',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 200
        assert body['data']['count'] == 1

    @patch('app.handlers.blocked_contacts.blocked_table')
    @patch('app.handlers.blocked_contacts.uuid')
    def test_lambda_handler_block_contact(self, mock_uuid, mock_table):
        """Test POST /admin/blocked endpoint."""
        mock_uuid.uuid4.return_value = '550e8400-e29b-41d4-a716-446655440000'
        mock_table.scan.return_value = {'Items': []}

        event = {
            'resource': '/admin/blocked',
            'path': '/admin/blocked',
            'httpMethod': 'POST',
            'body': json.dumps({
                'ip_address': '192.168.1.100',
                'user_agent': 'BadBot/1.0'
            }),
            'requestContext': {
                'resourcePath': '/admin/blocked',
                'httpMethod': 'POST'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['status'] == 201
        assert body['data']['blocked_contact']['ip_address'] == '192.168.1.100'

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_lambda_handler_unblock_contact(self, mock_table):
        """Test DELETE /admin/blocked/{id} endpoint."""
        blocked_id = '550e8400-e29b-41d4-a716-446655440000'
        mock_table.get_item.return_value = {
            'Item': {'id': blocked_id}
        }

        event = {
            'resource': '/admin/blocked/{blocked_id}',
            'path': f'/admin/blocked/{blocked_id}',
            'httpMethod': 'DELETE',
            'pathParameters': {'blocked_id': blocked_id},
            'requestContext': {
                'resourcePath': '/admin/blocked/{blocked_id}',
                'httpMethod': 'DELETE'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 200
        assert 'unblocked successfully' in body['data']['message']

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_lambda_handler_unblock_contact_not_found(self, mock_table):
        """Test DELETE /admin/blocked/{id} with non-existent ID."""
        mock_table.get_item.return_value = {}

        event = {
            'resource': '/admin/blocked/{blocked_id}',
            'path': '/admin/blocked/non-existent-id',
            'httpMethod': 'DELETE',
            'pathParameters': {'blocked_id': 'non-existent-id'},
            'requestContext': {
                'resourcePath': '/admin/blocked/{blocked_id}',
                'httpMethod': 'DELETE'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['status'] == 404
        assert 'not found' in body['error']


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_pydantic_validation_error_invalid_limit(self):
        """Test validation error for limit outside valid range."""
        from app.models.request_models import MessageQueryParams
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MessageQueryParams(limit=0)  # Below minimum

        with pytest.raises(ValidationError):
            MessageQueryParams(limit=101)  # Above maximum

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_block_contact_validation_error(self, mock_table):
        """Test POST /admin/blocked with invalid request body."""
        event = {
            'resource': '/admin/blocked',
            'path': '/admin/blocked',
            'httpMethod': 'POST',
            'body': json.dumps({
                # Missing required 'ip_address' field
                'user_agent': 'BadBot/1.0'
            }),
            'requestContext': {
                'resourcePath': '/admin/blocked',
                'httpMethod': 'POST'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 400
        assert 'Validation error' in body['error']

    @patch('app.handlers.blocked_contacts.blocked_table')
    def test_block_contact_value_error(
        self,
        mock_table,
        sample_blocked_contact_dict
    ):
        """Test ValueError handling for duplicate IP block."""
        mock_table.scan.return_value = {
            'Items': [sample_blocked_contact_dict]
        }

        event = {
            'resource': '/admin/blocked',
            'path': '/admin/blocked',
            'httpMethod': 'POST',
            'body': json.dumps({
                'ip_address': '10.0.0.1',  # Already blocked
                'user_agent': 'BadBot/1.0'
            }),
            'requestContext': {
                'resourcePath': '/admin/blocked',
                'httpMethod': 'POST'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 400
        assert 'already blocked' in body['error']

    @patch('app.handlers.messages.messages_table')
    def test_generic_exception_handling(self, mock_table):
        """Test generic exception returns 500 error."""
        mock_table.scan.side_effect = Exception("Database connection error")

        event = {
            'resource': '/admin/messages',
            'path': '/admin/messages',
            'httpMethod': 'GET',
            'queryStringParameters': {'limit': '50'},
            'requestContext': {
                'resourcePath': '/admin/messages',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['status'] == 500
        assert body['error'] == 'Internal server error'

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_value_error_handling(self, mock_table):
        """Test ValueError handling in list_messages endpoint."""
        event = {
            'resource': '/admin/messages',
            'path': '/admin/messages',
            'httpMethod': 'GET',
            'queryStringParameters': {
                'limit': '50',
                'next_token': 'invalid-token'
            },
            'requestContext': {
                'resourcePath': '/admin/messages',
                'httpMethod': 'GET'
            }
        }

        response = contact_admin_lambda.lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 400
        assert 'pagination token' in body['error']


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_contact_message_with_empty_strings(self):
        """Handle empty string values in ContactMessage."""
        message = ContactMessage(
            id='test-id',
            contact_email='',
            contact_message='Test',
            contact_name='',
            ip_address='127.0.0.1',
            user_agent='TestBot',
            timestamp=1697840000,
            is_blocked=0,
            contact_type='standard'
        )

        assert message.contact_email == ''
        assert message.contact_name == ''

    def test_blocked_contact_with_empty_user_agent(self):
        """Handle empty user_agent in BlockedContact."""
        blocked = BlockedContact(
            id='test-id',
            ip_address='127.0.0.1',
            user_agent='',
            is_blocked=1
        )

        assert blocked.user_agent == ''

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_with_max_limit(
        self,
        mock_table,
        sample_contact_message_dict
    ):
        """Test list_messages with maximum limit value."""
        mock_table.scan.return_value = {
            'Items': [sample_contact_message_dict] * 100
        }

        result = list_messages(limit=100)

        assert result.count == 100
        call_kwargs = mock_table.scan.call_args[1]
        assert call_kwargs['Limit'] == 100

    @patch('app.handlers.messages.messages_table')
    def test_list_messages_with_min_limit(
        self,
        mock_table,
        sample_contact_message_dict
    ):
        """Test list_messages with minimum limit value."""
        mock_table.scan.return_value = {
            'Items': [sample_contact_message_dict]
        }

        result = list_messages(limit=1)

        assert result.count == 1
        call_kwargs = mock_table.scan.call_args[1]
        assert call_kwargs['Limit'] == 1

    def test_block_contact_request_with_default_user_agent(self):
        """Test BlockContactRequest with default empty user_agent."""
        request = BlockContactRequest(ip_address='192.168.1.1')

        assert request.user_agent == ''

    @patch('app.handlers.messages.dynamodb')
    @patch('app.handlers.messages.messages_table')
    def test_get_stats_with_large_dataset(
        self,
        mock_messages_table,
        mock_dynamodb,
        sample_contact_message_dict
    ):
        """Test stats calculation with large number of messages."""
        # Create 1000 mock messages
        large_dataset = [sample_contact_message_dict.copy() for _ in range(1000)]

        mock_messages_table.scan.return_value = {
            'Items': large_dataset
        }

        # Mock blocked table
        mock_blocked_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_blocked_table
        mock_blocked_table.scan.return_value = {'Items': []}

        result = get_stats()

        assert result.total_messages == 1000

    def test_timestamp_boundaries(self):
        """Test ContactMessage with timestamp edge values."""
        # Very old timestamp
        old_message = ContactMessage(
            id='old-id',
            contact_message='Old message',
            ip_address='127.0.0.1',
            user_agent='TestBot',
            timestamp=0,  # Unix epoch
            is_blocked=0,
            contact_type='standard'
        )
        assert old_message.timestamp == 0

        # Far future timestamp
        future_message = ContactMessage(
            id='future-id',
            contact_message='Future message',
            ip_address='127.0.0.1',
            user_agent='TestBot',
            timestamp=2147483647,  # Max 32-bit int
            is_blocked=0,
            contact_type='standard'
        )
        assert future_message.timestamp == 2147483647
