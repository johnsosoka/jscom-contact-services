"""
DynamoDB helper utilities for converting between Pydantic models and DynamoDB items.

These utilities handle the bidirectional conversion between domain models and
DynamoDB item dictionaries, ensuring proper type handling.
"""

from typing import Any
from models.domain_models import ContactMessage, BlockedContact


def item_to_contact_message(item: dict[str, Any]) -> ContactMessage:
    """
    Convert a DynamoDB item to a ContactMessage domain model.

    Args:
        item: DynamoDB item dictionary

    Returns:
        ContactMessage instance populated from the item

    Note:
        Handles optional fields gracefully by defaulting to None if not present.
    """
    return ContactMessage(
        id=item['id'],
        contact_email=item.get('contact_email'),
        contact_message=item['contact_message'],
        contact_name=item.get('contact_name'),
        ip_address=item['ip_address'],
        user_agent=item['user_agent'],
        timestamp=int(item['timestamp']),
        is_blocked=int(item['is_blocked']),
        contact_type=item.get('contact_type', 'standard'),
        company_name=item.get('company_name'),
        industry=item.get('industry'),
    )


def item_to_blocked_contact(item: dict[str, Any]) -> BlockedContact:
    """
    Convert a DynamoDB item to a BlockedContact domain model.

    Args:
        item: DynamoDB item dictionary

    Returns:
        BlockedContact instance populated from the item
    """
    return BlockedContact(
        id=item['id'],
        ip_address=item['ip_address'],
        user_agent=item['user_agent'],
        is_blocked=int(item['is_blocked']),
    )


def contact_message_to_item(message: ContactMessage) -> dict[str, Any]:
    """
    Convert a ContactMessage domain model to a DynamoDB item dictionary.

    Args:
        message: ContactMessage instance

    Returns:
        Dictionary suitable for DynamoDB put_item operation

    Note:
        Excludes None values to avoid storing unnecessary attributes.
    """
    item = {
        'id': message.id,
        'contact_message': message.contact_message,
        'ip_address': message.ip_address,
        'user_agent': message.user_agent,
        'timestamp': message.timestamp,
        'is_blocked': message.is_blocked,
        'contact_type': message.contact_type,
    }

    # Add optional fields only if they have values
    if message.contact_email:
        item['contact_email'] = message.contact_email
    if message.contact_name:
        item['contact_name'] = message.contact_name
    if message.company_name:
        item['company_name'] = message.company_name
    if message.industry:
        item['industry'] = message.industry

    return item


def blocked_contact_to_item(blocked: BlockedContact) -> dict[str, Any]:
    """
    Convert a BlockedContact domain model to a DynamoDB item dictionary.

    Args:
        blocked: BlockedContact instance

    Returns:
        Dictionary suitable for DynamoDB put_item operation
    """
    return {
        'id': blocked.id,
        'ip_address': blocked.ip_address,
        'user_agent': blocked.user_agent,
        'is_blocked': blocked.is_blocked,
    }
