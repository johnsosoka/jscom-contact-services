"""
Response models for API endpoints.

These models define the structure of API responses with consistent formatting.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field
from models.domain_models import ContactMessage, BlockedContact


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

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "data": {"key": "value"},
                "error": None
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [],
                "next_token": "eyJpZCI6ICIuLi4ifQ==",
                "count": 50
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "total_messages": 1250,
                "blocked_count": 45,
                "unblocked_count": 1205,
                "total_blocked_ips": 12,
                "recent_messages_24h": 23,
                "consulting_messages": 320,
                "standard_messages": 930
            }
        }


class BlockedContactResponse(BaseModel):
    """
    Response for single blocked contact operations.

    Attributes:
        blocked_contact: The blocked contact record
        message: Optional status message
    """

    blocked_contact: BlockedContact = Field(description="Blocked contact record")
    message: str | None = Field(default=None, description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "blocked_contact": {
                    "id": "abc123",
                    "ip_address": "192.168.1.100",
                    "user_agent": "BadBot/1.0",
                    "is_blocked": 1
                },
                "message": "Contact blocked successfully"
            }
        }


class BlockedContactListResponse(BaseModel):
    """
    Response for listing blocked contacts.

    Attributes:
        blocked_contacts: List of blocked contact records
        count: Number of blocked contacts returned
    """

    blocked_contacts: list[BlockedContact] = Field(description="List of blocked contacts")
    count: int = Field(description="Number of blocked contacts")

    class Config:
        json_schema_extra = {
            "example": {
                "blocked_contacts": [],
                "count": 12
            }
        }
