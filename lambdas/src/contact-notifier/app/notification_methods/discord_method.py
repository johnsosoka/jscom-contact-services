"""
Discord notification method using webhook integration.
"""
import os
import json
import logging
import requests
from typing import Dict, Any
from .base import NotificationMethod

logger = logging.getLogger()


class DiscordNotificationMethod(NotificationMethod):
    """
    Discord notification implementation using webhook integration.
    """

    def __init__(self):
        """Initialize the Discord notification method with webhook URL."""
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')
        self.enabled = os.environ.get('DISCORD_ENABLED', 'false').lower() == 'true'

    def is_enabled(self) -> bool:
        """Check if Discord notifications are enabled via environment variable."""
        if not self.enabled:
            return False

        if not self.webhook_url:
            logger.warning("Discord is enabled but DISCORD_WEBHOOK_URL is not set")
            return False

        return True

    def get_method_name(self) -> str:
        """Return the method identifier."""
        return 'discord'

    def send_notification(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Discord notification via webhook.

        Args:
            contact_data: Dictionary containing contact information

        Returns:
            Dict with success status and message

        Raises:
            Exception: If Discord webhook fails to send
        """
        try:
            # Extract contact data
            contact_name = contact_data.get('contact_name', 'Unknown')
            contact_email = contact_data.get('contact_email', 'Unknown')
            contact_message = contact_data.get('contact_message', '')
            user_agent = contact_data.get('user_agent', 'Unknown')
            source_ip = contact_data.get('ip_address', 'Unknown')
            contact_type = contact_data.get('contact_type', 'standard')

            # Generate message based on contact type
            if contact_type == 'consulting':
                company_name = contact_data.get('company_name', 'N/A')
                industry = contact_data.get('industry', 'N/A')
                message_content = self._format_consulting_message(
                    contact_name, contact_email, contact_message,
                    user_agent, source_ip, company_name, industry
                )
            else:
                message_content = self._format_standard_message(
                    contact_name, contact_email, contact_message,
                    user_agent, source_ip
                )

            # Send to Discord webhook
            status_code = self._post_to_discord_webhook(self.webhook_url, message_content)

            logger.info(f"Discord notification sent successfully. Status: {status_code}")

            return {
                'success': True,
                'message': f"Discord notification sent successfully. Status: {status_code}",
                'status_code': status_code
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to send Discord notification',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error sending Discord notification: {str(e)}")
            return {
                'success': False,
                'message': 'Unexpected error sending Discord notification',
                'error': str(e)
            }

    def _post_to_discord_webhook(self, webhook_url: str, content: str) -> int:
        """
        Post message to Discord webhook.

        Args:
            webhook_url: Discord webhook URL
            content: Message content to send

        Returns:
            HTTP status code from Discord API

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        payload = {"content": content}
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.status_code

    def _format_standard_message(self, contact_name: str, contact_email: str,
                                  contact_message: str, user_agent: str,
                                  source_ip: str) -> str:
        """Format standard contact message for Discord."""
        message = f"""**New Contact Message!**

**Name:** {contact_name}
**Email:** {contact_email}
**Message:**
{contact_message}

---
**User Agent:** {user_agent}
**Source IP:** {source_ip}

John Has Been Contacted."""
        return message

    def _format_consulting_message(self, contact_name: str, contact_email: str,
                                    contact_message: str, user_agent: str,
                                    source_ip: str, company_name: str,
                                    industry: str) -> str:
        """Format consulting contact message for Discord."""
        message = f"""**New Consulting Contact Message!**

**Name:** {contact_name}
**Email:** {contact_email}
**Company:** {company_name}
**Industry:** {industry}
**Message:**
{contact_message}

---
**User Agent:** {user_agent}
**Source IP:** {source_ip}

John Has Been Consulted!"""
        return message
