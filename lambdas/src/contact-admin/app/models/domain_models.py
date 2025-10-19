"""
Domain models representing DynamoDB entities.

These models map directly to the structure of items stored in DynamoDB tables.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ContactMessage(BaseModel):
    """
    Represents a contact form submission stored in the all-contact-messages table.

    Attributes:
        id: Unique identifier for the message
        contact_email: Email address of the sender
        contact_message: The message content
        contact_name: Name of the sender
        ip_address: IP address of the sender
        user_agent: User agent string from the request
        timestamp: Unix timestamp (seconds since epoch)
        is_blocked: Whether this message came from a blocked IP (0 or 1)
        contact_type: Type of contact form submission
        company_name: Optional company name (consulting contacts only)
        industry: Optional industry field (consulting contacts only)
    """

    id: str = Field(description="Unique message identifier")
    contact_email: str | None = Field(default=None, description="Sender email address")
    contact_message: str = Field(description="Message content")
    contact_name: str | None = Field(default=None, description="Sender name")
    ip_address: str = Field(description="Sender IP address")
    user_agent: str = Field(description="Sender user agent")
    timestamp: int = Field(description="Message timestamp (Unix seconds)")
    is_blocked: int = Field(description="Blocked status (0 or 1)")
    contact_type: Literal["standard", "consulting"] = Field(
        default="standard",
        description="Contact form type"
    )
    company_name: str | None = Field(default=None, description="Company name (consulting only)")
    industry: str | None = Field(default=None, description="Industry (consulting only)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "contact_email": "john@example.com",
                "contact_message": "Interested in your services",
                "contact_name": "John Doe",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "timestamp": 1697840000,
                "is_blocked": 0,
                "contact_type": "standard"
            }
        }


class BlockedContact(BaseModel):
    """
    Represents a blocked contact entry in the blocked_contacts table.

    Attributes:
        id: Unique identifier for the blocked contact record
        ip_address: The blocked IP address
        user_agent: User agent string associated with the block
        is_blocked: Block status (0 or 1, typically 1 for entries in this table)
    """

    id: str = Field(description="Unique blocked contact identifier")
    ip_address: str = Field(description="Blocked IP address")
    user_agent: str = Field(description="Associated user agent")
    is_blocked: int = Field(description="Block status (0 or 1)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "ip_address": "192.168.1.100",
                "user_agent": "BadBot/1.0",
                "is_blocked": 1
            }
        }
