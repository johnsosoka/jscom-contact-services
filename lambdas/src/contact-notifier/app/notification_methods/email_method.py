"""
Email notification method using AWS SES.
"""
import os
import boto3
import logging
from typing import Dict, Any
from .base import NotificationMethod

logger = logging.getLogger()


class EmailNotificationMethod(NotificationMethod):
    """
    Email notification implementation using AWS SES.
    """

    def __init__(self):
        """Initialize the email notification method with SES client."""
        self.ses = boto3.client('ses')
        self.sender = os.environ.get('EMAIL_SENDER', 'mail@johnsosoka.com')
        self.recipient = os.environ.get('EMAIL_RECIPIENT', 'im@johnsosoka.com')
        self.enabled = os.environ.get('EMAIL_ENABLED', 'true').lower() == 'true'

    def is_enabled(self) -> bool:
        """Check if email notifications are enabled via environment variable."""
        return self.enabled

    def get_method_name(self) -> str:
        """Return the method identifier."""
        return 'email'

    def send_notification(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email notification via AWS SES.

        Args:
            contact_data: Dictionary containing contact information

        Returns:
            Dict with success status and message

        Raises:
            Exception: If email fails to send
        """
        try:
            # Extract contact data
            contact_name = contact_data.get('contact_name', 'Unknown')
            contact_email = contact_data.get('contact_email', 'Unknown')
            contact_message = contact_data.get('contact_message', '')
            user_agent = contact_data.get('user_agent', 'Unknown')
            source_ip = contact_data.get('ip_address', 'Unknown')
            contact_type = contact_data.get('contact_type', 'standard')

            # Generate email based on contact type
            if contact_type == 'consulting':
                company_name = contact_data.get('company_name', 'N/A')
                industry = contact_data.get('industry', 'N/A')
                email_subject, email_body = self._generate_consulting_email(
                    contact_name, contact_email, contact_message,
                    user_agent, source_ip, company_name, industry
                )
            else:
                email_subject, email_body = self._generate_standard_email(
                    contact_name, contact_email, contact_message,
                    user_agent, source_ip
                )

            # Send via SES
            response = self.ses.send_email(
                Source=self.sender,
                Destination={'ToAddresses': [self.recipient]},
                Message={
                    'Subject': {'Data': email_subject},
                    'Body': {'Html': {'Data': email_body}}
                }
            )

            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")

            return {
                'success': True,
                'message': f"Email sent successfully. MessageId: {response['MessageId']}",
                'message_id': response['MessageId']
            }

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to send email notification',
                'error': str(e)
            }

    def _generate_standard_email(self, contact_name: str, contact_email: str,
                                 contact_message: str, user_agent: str,
                                 source_ip: str) -> tuple[str, str]:
        """Generate standard contact email template."""
        email_subject = 'New Contact Message.'
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
        return email_subject, email_body

    def _generate_consulting_email(self, contact_name: str, contact_email: str,
                                   contact_message: str, user_agent: str,
                                   source_ip: str, company_name: str,
                                   industry: str) -> tuple[str, str]:
        """Generate consulting contact email template."""
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
        return email_subject, email_body
