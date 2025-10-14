"""
Base class for notification methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class NotificationMethod(ABC):
    """
    Abstract base class for notification methods.

    All notification method implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if this notification method is enabled.

        Implementations should check environment variables or configuration
        to determine if the method should be used.

        Returns:
            bool: True if the notification method is enabled, False otherwise
        """
        pass

    @abstractmethod
    def send_notification(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a notification using this method.

        Args:
            contact_data: Dictionary containing contact information including:
                - contact_name: Name of the person contacting
                - contact_email: Email address of the person
                - contact_message: The message content
                - contact_type: Type of contact ('standard' or 'consulting')
                - user_agent: User agent string
                - ip_address: Source IP address
                - company_name: (optional) Company name for consulting contacts
                - industry: (optional) Industry for consulting contacts

        Returns:
            Dict containing:
                - success: bool indicating if notification was sent successfully
                - message: str describing the result
                - error: (optional) str error message if failed

        Raises:
            Exception: If notification fails to send
        """
        pass

    @abstractmethod
    def get_method_name(self) -> str:
        """
        Get the name/identifier of this notification method.

        Returns:
            str: Name of the method (e.g., 'email', 'discord', 'slack')
        """
        pass
