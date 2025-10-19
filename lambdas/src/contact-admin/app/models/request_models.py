"""
Request models for API endpoints.

These models define the structure of incoming request payloads and query parameters.
"""

from pydantic import BaseModel, Field


class BlockContactRequest(BaseModel):
    """
    Request body for blocking a contact by IP address.

    Attributes:
        ip_address: The IP address to block
        user_agent: Optional user agent to associate with the block
    """

    ip_address: str = Field(description="IP address to block")
    user_agent: str = Field(default="", description="User agent associated with block")

    class Config:
        json_schema_extra = {
            "example": {
                "ip_address": "192.168.1.100",
                "user_agent": "BadBot/1.0"
            }
        }


class MessageQueryParams(BaseModel):
    """
    Query parameters for listing messages with pagination.

    Attributes:
        limit: Maximum number of messages to return
        next_token: Pagination token for retrieving next page
        contact_type: Optional filter by contact type
    """

    limit: int = Field(default=50, ge=1, le=100, description="Max messages per page")
    next_token: str | None = Field(default=None, description="Pagination token")
    contact_type: str | None = Field(default=None, description="Filter by contact type")

    class Config:
        json_schema_extra = {
            "example": {
                "limit": 50,
                "next_token": "eyJpZCI6ICIuLi4ifQ==",
                "contact_type": "consulting"
            }
        }
