import json
import boto3
import os

sqs = boto3.client('sqs')
queue_url = os.environ['CONTACT_MESSAGE_QUEUE_URL']


def lambda_handler(event, context):
    # Extract fields from payload
    payload = json.loads(event['body'])
    contact_email = payload.get('contact_email')
    contact_message = payload.get('contact_message')
    contact_name = payload.get('contact_name')

    # Extract IP address and user agent from event
    ip_address = event['requestContext']['identity']['sourceIp']
    user_agent = event['requestContext']['identity']['userAgent']

    # Validate required fields
    if not contact_message:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'contact_message is a required field'})
        }

    # Publish message to SQS queue with IP address and user agent
    message = {
        'contact_email': contact_email,
        'contact_message': contact_message,
        'contact_name': contact_name,
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Message Received. Currently Processing'})
    }
