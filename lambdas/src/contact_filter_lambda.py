import json
import boto3
import os
import logging
import uuid
import datetime

# Get resource IDs from environment variables
blocked_contacts_table_name = os.environ['BLOCKED_CONTACTS_TABLE_NAME']
all_contact_messages_table_name = os.environ['ALL_CONTACT_MESSAGES_TABLE_NAME']
contact_notify_queue_url = os.environ['CONTACT_NOTIFY_QUEUE_URL']
contact_message_queue_url = os.environ['CONTACT_MESSAGE_QUEUE_URL']

# Create DynamoDB clients
dynamodb = boto3.client('dynamodb')
blocked_contacts_table = boto3.resource('dynamodb').Table(blocked_contacts_table_name)
all_contact_messages_table = boto3.resource('dynamodb').Table(all_contact_messages_table_name)

# Create SQS client
sqs = boto3.client('sqs')

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # Loop through messages in SQS queue
    for message in event['Records']:
        # Parse message body
        message_body = json.loads(message['body'])

        # Extract message fields
        contact_email = message_body.get('contact_email')
        contact_message = message_body.get('contact_message')
        contact_name = message_body.get('contact_name')
        ip_address = message_body.get('ip_address')
        user_agent = message_body.get('user_agent')

        # Check if IP address is blocked
        is_blocked = False
        # Create the KeyConditionExpression for the query
        # Create the FilterExpression for the scan
        filter_expression = 'ip_address = :ip_address'
        expression_attribute_values = {
            ':ip_address': {'S': ip_address}
        }

        # Scan the table for items with the specified IP address
        response = blocked_contacts_table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        if len(response['Items']) > 0:
            is_blocked = True
            logger.info(f'IP address {ip_address} is blocked')

        timestamp = datetime.datetime.now()
        # Insert message into all_contact_messages table
        all_contact_messages_table.put_item(
            Item={
                'id': str(uuid.uuid4()),
                'contact_email': contact_email,
                'contact_message': contact_message,
                'contact_name': contact_name,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': int(timestamp.timestamp()),
                'is_blocked': int(is_blocked)
            }
        )

        # Publish message to contact_notify_queue if IP address is not blocked
        if not is_blocked:
            print("Contact isn't blocked. Sending to notification queue")
            response = sqs.send_message(
                QueueUrl=contact_notify_queue_url,
                MessageBody=json.dumps(message_body)
            )
            logger.info(f'Message sent to contact_notify_queue: {response["MessageId"]}')

        # Delete message from the queue
        sqs.delete_message(
            QueueUrl=contact_message_queue_url,
            ReceiptHandle=message['receiptHandle']
        )

