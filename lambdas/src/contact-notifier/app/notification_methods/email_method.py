"""
Email notification method using AWS SES.
"""
import os
import boto3
import logging
from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .base import NotificationMethod

logger = logging.getLogger()


class EmailNotificationMethod(NotificationMethod):
    """
    Email notification implementation using AWS SES.
    """

    def __init__(self):
        """Initialize the email notification method with SES client and Jinja2 environment."""
        self.ses = boto3.client('ses')
        self.sender = os.environ.get('EMAIL_SENDER', 'mail@johnsosoka.com')
        self.recipient = os.environ.get('EMAIL_RECIPIENT', 'im@johnsosoka.com')
        self.enabled = os.environ.get('EMAIL_ENABLED', 'true').lower() == 'true'

        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / 'templates'
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

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

            # Skip email notifications for homelab-alert types (Discord only)
            if contact_type == 'homelab-alert':
                logger.info("Skipping email notification for homelab-alert (Discord only)")
                return {
                    'success': True,
                    'message': 'Email skipped for homelab-alert type (Discord only)',
                    'skipped': True
                }

            # Generate email based on contact type
            if contact_type == 'consulting':
                company_name = contact_data.get('company_name', 'N/A')
                industry = contact_data.get('industry', 'N/A')
                email_subject, email_body = self._generate_consulting_email(
                    contact_name, contact_email, contact_message,
                    user_agent, source_ip, company_name, industry
                )
            elif contact_type == 'standard':
                email_subject, email_body = self._generate_standard_email(
                    contact_name, contact_email, contact_message,
                    user_agent, source_ip
                )
            else:
                # For unknown types, skip email gracefully
                logger.warning(f"Unknown contact_type: {contact_type}, skipping email")
                return {
                    'success': True,
                    'message': f'Email skipped for unknown type: {contact_type}',
                    'skipped': True
                }

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
        """Generate standard contact email from Jinja2 template."""
        email_subject = 'New Contact Message.'

        template = self.jinja_env.get_template('standard_email_template.html')
        email_body = template.render(
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
        """Generate consulting contact email from Jinja2 template."""
        email_subject = 'New Consulting Contact Message!'

        template = self.jinja_env.get_template('consulting_email_template.html')
        email_body = template.render(
            contact_name=contact_name,
            contact_email=contact_email,
            company_name=company_name,
            industry=industry,
            contact_message=contact_message,
            user_agent=user_agent,
            source_ip=source_ip
        )

        return email_subject, email_body
