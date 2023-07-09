import json
import boto3
import os
import base64

sqs = boto3.client('sqs')
queue_url = os.environ['CONTACT_MESSAGE_QUEUE_URL']


def lambda_handler(event, context):
    # decode if body is base64 encoded
    if event['isBase64Encoded']:
        decoded_str = base64.b64decode(event['body']).decode('utf-8')
        payload = json.loads(decoded_str)
    else:
        payload = json.loads(event['body'])

    contact_email = payload.get('contact_email')
    contact_message = payload.get('contact_message')
    contact_name = payload.get('contact_name')

    # # Extract IP address and user agent from event
    # these vars are different depending on the event source, commenting out since routing from api gateway
    # ip_address = event['requestContext']['identity']['sourceIp']
    # user_agent = event['requestContext']['identity']['userAgent']
    ip_address = event['requestContext']['http']['sourceIp']
    user_agent = event['requestContext']['http']['userAgent']

    # Validate required fields
    if not contact_message:
        print("contact_message is a required field & is missing.")
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
