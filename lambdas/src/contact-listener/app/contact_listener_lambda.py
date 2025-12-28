import json
import boto3
import os
import base64
from app.turnstile import validate_turnstile

sqs = boto3.client('sqs')
queue_url = os.environ['CONTACT_MESSAGE_QUEUE_URL']

def lambda_handler(event, context):
    # decode if body is base64 encoded
    if event['isBase64Encoded']:
        decoded_str = base64.b64decode(event['body']).decode('utf-8')
        payload = json.loads(decoded_str)
    else:
        payload = json.loads(event['body'])

    # Extract IP address and user agent from event
    ip_address = event['requestContext']['http']['sourceIp']
    user_agent = event['requestContext']['http']['userAgent']

    # Extract Turnstile parameters
    turnstile_token = payload.get('turnstile_token')
    turnstile_site = payload.get('turnstile_site')

    # Validate Turnstile token presence
    if not turnstile_token:
        print("Turnstile token is missing")
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Security verification required'})
        }

    # Validate Turnstile token
    if not validate_turnstile(turnstile_token, ip_address, turnstile_site or ''):
        print(f"Turnstile validation failed for IP: {ip_address}")
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Security verification failed'})
        }

    contact_email = payload.get('contact_email')
    contact_message = payload.get('contact_message')
    contact_name = payload.get('contact_name')

    # Validate required fields
    if not contact_message:
        print("contact_message is a required field & is missing.")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'contact_message is a required field'})
        }

    # Check if payload is from consulting contact form
    if payload.get('consulting_contact'):
        company_name = payload.get('company_name')
        industry = payload.get('industry')

        # Construct message for consulting contact form
        message = {
            'contact_email': contact_email,
            'contact_message': contact_message,
            'contact_name': contact_name,
            'company_name': company_name,
            'industry': industry,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'contact_type': 'consulting'
        }
    else:
        # Construct message for standard contact form
        message = {
            'contact_email': contact_email,
            'contact_message': contact_message,
            'contact_name': contact_name,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'contact_type': 'standard'
        }

    print(f'Publishing message to SQS queue: {message}')

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Message Received. Currently Processing'})
    }
