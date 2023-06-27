import json
import os
import pytest
from unittest.mock import MagicMock, patch

# Import the Lambda function
import src.contact_listener as contact_listener


@pytest.fixture
def sqs_client():
    # Create a mock SQS client
    sqs = MagicMock()
    sqs.send_message.return_value = {'MessageId': '1234'}
    return sqs


@patch.dict(os.environ, {'SQS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/my-queue'})
def test_lambda_handler_success(sqs_client):
    # Define a sample event payload
    event = {
        'body': json.dumps({
            'contact_email': 'test@example.com',
            'contact_message': 'Hello, world!',
            'contact_name': 'Test User'
        })
    }

    # Call the Lambda function
    response = lambda_handler(event, None)

    # Verify that the message was sent to the SQS queue
    sqs_client.send_message.assert_called_with(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/my-queue',
        MessageBody=json.dumps({
            'contact_email': 'test@example.com',
            'contact_message': 'Hello, world!',
            'contact_name': 'Test User'
        })
    )

    # Verify that the Lambda function returns a success response
    assert response['statusCode'] == 200
    assert response['body'] == json.dumps({'message': 'Message sent to SQS queue'})


def test_lambda_handler_missing_required_field(sqs_client):
    # Define a sample event payload with a missing required field
    event = {
        'body': json.dumps({
            'contact_email': 'test@example.com',
            'contact_name': 'Test User'
        })
    }

    # Call the Lambda function
    response = lambda_handler(event, None)

    # Verify that the Lambda function returns a validation error response
    assert response['statusCode'] == 400
    assert 'contact_message is a required field' in response['body']
