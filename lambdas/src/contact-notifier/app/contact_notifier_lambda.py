import json
import boto3
import os

# Get queue URL from environment variable
queue_url = os.environ['CONTACT_NOTIFY_QUEUE']

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
            'body': 'Missing required field: contact_message'
        }

    # Populate fields for the email
    contact_name = message_body.get('contact_name', 'Unknown')
    contact_email = message_body.get('contact_email', 'Unknown')
    user_agent = message_body.get('user_agent', 'Unknown')
    source_ip = message_body.get('ip_address', 'Unknown')
    company_name = message_body.get('company_name', 'N/A')
    industry = message_body.get('industry', 'N/A')
    contact_type = message_body.get('contact_type', 'standard')
    llm_classification_type = message_body.get('llm_classification_type', 'N/A')
    llm_classification_priority = message_body.get('llm_classification_priority', 'N/A')
    llm_confidence_score = message_body.get('llm_confidence_score', 'N/A')

    # Create the HTML email template
    if contact_type == 'consulting':
        email_subject = 'New Consulting Contact Message!'
        email_body = """
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f4f4f4;
                    }}
                    .container {{
                        width: 100%;
                        padding: 20px;
                        background-color: #ffffff;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        margin: auto;
                        max-width: 600px;
                    }}
                    .header {{
                        background-color: #0073e6;
                        color: white;
                        padding: 10px 0;
                        text-align: center;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                    .content p {{
                        margin: 10px 0;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 10px 0;
                        color: #777;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>New Consulting Contact Message!</h1>
                    </div>
                    <div class="content">
                        <p><strong>Name:</strong> {contact_name}</p>
                        <p><strong>Email:</strong> {contact_email}</p>
                        <p><strong>Company:</strong> {company_name}</p>
                        <p><strong>Industry:</strong> {industry}</p>
                        <p><strong>Message:</strong> {contact_message}</p>
                        <hr>
                        <p><strong>User Agent:</strong> {user_agent}</p>
                        <p><strong>Source IP:</strong> {source_ip}</p>
                    </div>
                    <div class="footer">
                        <p>John Has Been Consulted!</p>
                    </div>
                </div>
            </body>
            </html>
        """.format(
            contact_name=contact_name,
            contact_email=contact_email,
            company_name=company_name,
            industry=industry,
            contact_message=contact_message,
            user_agent=user_agent,
            source_ip=source_ip
        )
    else:
        email_subject = f'New Contact Message. {llm_classification_type}'
        email_body = """
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f4f4f4;
                    }}
                    .container {{
                        width: 100%;
                        padding: 20px;
                        background-color: #ffffff;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        margin: auto;
                        max-width: 600px;
                    }}
                    .header {{
                        background-color: #0073e6;
                        color: white;
                        padding: 10px 0;
                        text-align: center;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                    .content p {{
                        margin: 10px 0;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 10px 0;
                        color: #777;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>New Contact Message!</h1>
                    </div>
                    <div class="content">
                        <p><strong>Name:</strong> {contact_name}</p>
                        <p><strong>Email:</strong> {contact_email}</p>
                        <p><strong>Message:</strong> {contact_message}</p>
                        <hr>
                        <p><strong>User Agent:</strong> {user_agent}</p>
                        <p><strong>Source IP:</strong> {source_ip}</p>
                    </div>
                    <div class="footer">
                        <p>John Has Been Contacted.</p>
                    </div>
                </div>
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
