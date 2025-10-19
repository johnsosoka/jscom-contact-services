"""
Admin API Lambda function for managing contact messages and blocked contacts.

This Lambda provides REST API endpoints for administrative operations on the
contact form system, including viewing messages, managing blocked IPs, and
retrieving system statistics.

Environment Variables:
    ALL_CONTACT_MESSAGES_TABLE_NAME: DynamoDB table for contact messages
    BLOCKED_CONTACTS_TABLE_NAME: DynamoDB table for blocked contacts
"""

import json
from typing import Any
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths
from pydantic import ValidationError

from models import (
    ApiResponse,
    MessageListResponse,
    StatsResponse,
    BlockContactRequest,
    BlockedContactResponse,
    BlockedContactListResponse,
    MessageQueryParams,
)
from handlers import (
    list_messages,
    get_message_by_id,
    get_stats,
    list_blocked_contacts,
    block_contact,
    unblock_contact,
)

# Initialize logger and API resolver
logger = Logger()
app = APIGatewayHttpResolver()


@app.get("/admin/messages")
def handle_list_messages() -> dict[str, Any]:
    """
    List contact messages with pagination.

    Query Parameters:
        limit (int): Max messages per page (1-100, default 50)
        next_token (str): Pagination token for next page
        contact_type (str): Filter by 'standard' or 'consulting'

    Returns:
        200: MessageListResponse with messages and pagination
        400: Validation error
        500: Internal server error
    """
    try:
        # Parse query parameters
        query_params = MessageQueryParams(
            limit=int(app.current_event.get_query_string_value("limit", "50")),
            next_token=app.current_event.get_query_string_value("next_token"),
            contact_type=app.current_event.get_query_string_value("contact_type"),
        )

        # Get messages
        result = list_messages(
            limit=query_params.limit,
            next_token=query_params.next_token,
            contact_type=query_params.contact_type,
        )

        response = ApiResponse[MessageListResponse](
            status=200,
            data=result
        )

        return response.model_dump()

    except ValidationError as e:
        logger.error(f"Validation error in list_messages: {e}")
        response = ApiResponse[None](
            status=400,
            error=f"Validation error: {str(e)}"
        )
        return response.model_dump()

    except ValueError as e:
        logger.error(f"Value error in list_messages: {e}")
        response = ApiResponse[None](
            status=400,
            error=str(e)
        )
        return response.model_dump()

    except Exception as e:
        logger.exception(f"Error in list_messages: {e}")
        response = ApiResponse[None](
            status=500,
            error="Internal server error"
        )
        return response.model_dump()


@app.get("/admin/messages/<message_id>")
def handle_get_message(message_id: str) -> dict[str, Any]:
    """
    Retrieve a specific contact message by ID.

    Path Parameters:
        message_id (str): Unique message identifier

    Returns:
        200: ContactMessage details
        404: Message not found
        500: Internal server error
    """
    try:
        message = get_message_by_id(message_id)

        if message is None:
            response = ApiResponse[None](
                status=404,
                error=f"Message not found: {message_id}"
            )
            return response.model_dump()

        response = ApiResponse(
            status=200,
            data=message
        )

        return json.loads(response.model_dump_json())

    except Exception as e:
        logger.exception(f"Error in get_message: {e}")
        response = ApiResponse[None](
            status=500,
            error="Internal server error"
        )
        return response.model_dump()


@app.get("/admin/stats")
def handle_get_stats() -> dict[str, Any]:
    """
    Get system statistics and analytics.

    Returns:
        200: StatsResponse with system metrics
        500: Internal server error
    """
    try:
        stats = get_stats()

        response = ApiResponse[StatsResponse](
            status=200,
            data=stats
        )

        return response.model_dump()

    except Exception as e:
        logger.exception(f"Error in get_stats: {e}")
        response = ApiResponse[None](
            status=500,
            error="Internal server error"
        )
        return response.model_dump()


@app.get("/admin/blocked")
def handle_list_blocked() -> dict[str, Any]:
    """
    List all blocked contacts.

    Returns:
        200: BlockedContactListResponse with all blocked contacts
        500: Internal server error
    """
    try:
        result = list_blocked_contacts()

        response = ApiResponse[BlockedContactListResponse](
            status=200,
            data=result
        )

        return response.model_dump()

    except Exception as e:
        logger.exception(f"Error in list_blocked: {e}")
        response = ApiResponse[None](
            status=500,
            error="Internal server error"
        )
        return response.model_dump()


@app.post("/admin/blocked")
def handle_block_contact() -> dict[str, Any]:
    """
    Add an IP address to the blocked list.

    Request Body:
        {
            "ip_address": "192.168.1.100",
            "user_agent": "BadBot/1.0"
        }

    Returns:
        201: BlockedContactResponse with created record
        400: Validation error or IP already blocked
        500: Internal server error
    """
    try:
        # Parse request body
        body = app.current_event.json_body
        request = BlockContactRequest(**body)

        # Block the contact
        blocked = block_contact(request)

        response = ApiResponse[BlockedContactResponse](
            status=201,
            data=BlockedContactResponse(
                blocked_contact=blocked,
                message="Contact blocked successfully"
            )
        )

        return response.model_dump()

    except ValidationError as e:
        logger.error(f"Validation error in block_contact: {e}")
        response = ApiResponse[None](
            status=400,
            error=f"Validation error: {str(e)}"
        )
        return response.model_dump()

    except ValueError as e:
        logger.error(f"Value error in block_contact: {e}")
        response = ApiResponse[None](
            status=400,
            error=str(e)
        )
        return response.model_dump()

    except Exception as e:
        logger.exception(f"Error in block_contact: {e}")
        response = ApiResponse[None](
            status=500,
            error="Internal server error"
        )
        return response.model_dump()


@app.delete("/admin/blocked/<blocked_id>")
def handle_unblock_contact(blocked_id: str) -> dict[str, Any]:
    """
    Remove an IP address from the blocked list.

    Path Parameters:
        blocked_id (str): ID of the blocked contact record

    Returns:
        200: Success message
        404: Blocked contact not found
        500: Internal server error
    """
    try:
        success = unblock_contact(blocked_id)

        if not success:
            response = ApiResponse[None](
                status=404,
                error=f"Blocked contact not found: {blocked_id}"
            )
            return response.model_dump()

        response = ApiResponse(
            status=200,
            data={"message": "Contact unblocked successfully"}
        )

        return response.model_dump()

    except Exception as e:
        logger.exception(f"Error in unblock_contact: {e}")
        response = ApiResponse[None](
            status=500,
            error="Internal server error"
        )
        return response.model_dump()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Main Lambda handler for admin API requests.

    Args:
        event: API Gateway HTTP API event
        context: Lambda context object

    Returns:
        API Gateway response with status code and body
    """
    logger.info(f"Received event: {json.dumps(event)}")

    return app.resolve(event, context)
