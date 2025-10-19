"""
Notification methods package for contact notifier lambda.
"""
from .base import NotificationMethod
from .email_method import EmailNotificationMethod
from .discord_method import DiscordNotificationMethod

__all__ = ['NotificationMethod', 'EmailNotificationMethod', 'DiscordNotificationMethod']
