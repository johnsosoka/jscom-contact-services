import json
import boto3
import os

# Get queue URL from environment variable
queue_url = os.environ['CONTACT_MESSAGE_QUEUE_URL']

def lambda_handler(event, context):
    # Get the message from the event
    message = event['Records'][0]['body']

    # Parse the message body
    message_body = json.loads(message)

    # Validate the required field
    contact_message = message_body.get('contact_message')
    if not contact_message:
        return {
            'statusCode': 400,
            'body': 'Missing required field: contactMessage'
        }

    # Populate fields for the email
    contact_name = message_body.get('contact_name', 'Unknown')
    contact_email = message_body.get('contact_email', 'Unknown')
    user_agent = message_body.get('user_agent', 'Unknown')
    source_ip = message_body.get('ip_address', 'Unknown')

    # Create the HTML email template
    email_subject = 'New Contact Message'
    email_body = """
        <html>
        <head></head>
        <body>
            <h1>New Contact Message</h1>
            <p><strong>Name:</strong> {contact_name}</p>
            <p><strong>Email:</strong> {contact_email}</p>
            <p><strong>Message:</strong> {contact_message}</p>
            <p><strong>User Agent:</strong> {user_agent}</p>
            <p><strong>Source IP:</strong> {source_ip}</p>
        </body>
        </html>
    """.format(
        contact_name=contact_name,
        contact_email=contact_email,
        contact_message=contact_message,
        user_agent=user_agent,
        source_ip=source_ip
    )

    # Send the email using Amazon SES
    ses = boto3.client('ses')
    ses.send_email(
        Source='mail@johnsosoka.com',
        Destination={'ToAddresses': ['im@johnsosoka.com']},
        Message={
            'Subject': {'Data': email_subject},
            'Body': {'Html': {'Data': email_body}}
        }
    )

    # Delete the message from the queue
    sqs = boto3.client('sqs')
    receipt_handle = event['Records'][0]['receiptHandle']
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print("Sent email")

    return {
        'statusCode': 200,
        'body': 'Email sent successfully'
    }
