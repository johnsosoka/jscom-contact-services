"""
Response models for API endpoints.

These models define the structure of API responses with consistent formatting.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field
from models.contact_models import ContactMessage, BlockedContact


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    Generic API response wrapper providing consistent structure.

    Attributes:
        status: HTTP status code
        data: Response payload (type varies by endpoint)
        error: Error message if request failed
    """

    status: int = Field(description="HTTP status code")
    data: T | None = Field(default=None, description="Response data")
    error: str | None = Field(default=None, description="Error message")


class MessageListResponse(BaseModel):
    """
    Response for message listing endpoint with pagination support.

    Attributes:
        messages: List of contact messages
        next_token: Token for retrieving next page (null if no more pages)
        count: Number of messages in current response
    """

    messages: list[ContactMessage] = Field(description="List of contact messages")
    next_token: str | None = Field(default=None, description="Pagination token")
    count: int = Field(description="Number of messages returned")


class StatsResponse(BaseModel):
    """
    Response for statistics endpoint providing system metrics.

    Attributes:
        total_messages: Total number of messages in system
        blocked_count: Number of messages from blocked IPs
        unblocked_count: Number of messages from non-blocked IPs
        total_blocked_ips: Total number of blocked IP addresses
        recent_messages_24h: Number of messages received in last 24 hours
        consulting_messages: Total consulting-type messages
        standard_messages: Total standard-type messages
    """

    total_messages: int = Field(description="Total messages in system")
    blocked_count: int = Field(description="Messages from blocked IPs")
    unblocked_count: int = Field(description="Messages from non-blocked IPs")
    total_blocked_ips: int = Field(description="Total blocked IP addresses")
    recent_messages_24h: int = Field(description="Messages in last 24 hours")
    consulting_messages: int = Field(description="Total consulting messages")
    standard_messages: int = Field(description="Total standard messages")


class BlockedContactResponse(BaseModel):
    """
    Response for single blocked contact operations.

    Attributes:
        blocked_contact: The blocked contact record
        message: Optional status message
    """

    blocked_contact: BlockedContact = Field(description="Blocked contact record")
    message: str | None = Field(default=None, description="Status message")


class BlockedContactListResponse(BaseModel):
    """
    Response for listing blocked contacts.

    Attributes:
        blocked_contacts: List of blocked contact records
        count: Number of blocked contacts returned
    """

    blocked_contacts: list[BlockedContact] = Field(description="List of blocked contacts")
    count: int = Field(description="Number of blocked contacts")
