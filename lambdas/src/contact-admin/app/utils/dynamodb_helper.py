"""
Simplified DynamoDB helper utilities.

Since boto3 resource API returns native Python types, we can use Pydantic's
model_validate() directly with minimal transformation.
"""

from typing import Any
from models.contact_models import ContactMessage, BlockedContact


def item_to_contact_message(item: dict[str, Any]) -> ContactMessage:
    """
    Convert a DynamoDB item to a ContactMessage model.

    Boto3 resource API returns native types, so we just validate with Pydantic.
    """
    return ContactMessage.model_validate(item)


def item_to_blocked_contact(item: dict[str, Any]) -> BlockedContact:
    """
    Convert a DynamoDB item to a BlockedContact model.

    Boto3 resource API returns native types, so we just validate with Pydantic.
    """
    return BlockedContact.model_validate(item)


def contact_message_to_item(message: ContactMessage) -> dict[str, Any]:
    """
    Convert a ContactMessage to a DynamoDB item dictionary.

    Uses Pydantic's model_dump() and excludes None values.
    """
    return message.model_dump(exclude_none=True)


def blocked_contact_to_item(blocked: BlockedContact) -> dict[str, Any]:
    """
    Convert a BlockedContact to a DynamoDB item dictionary.

    Uses Pydantic's model_dump() and excludes None values.
    """
    return blocked.model_dump(exclude_none=True)
