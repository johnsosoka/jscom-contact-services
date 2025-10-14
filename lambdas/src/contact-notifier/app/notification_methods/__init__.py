"""
Notification methods package for contact notifier lambda.
"""
from .base import NotificationMethod
from .email_method import EmailNotificationMethod

__all__ = ['NotificationMethod', 'EmailNotificationMethod']
