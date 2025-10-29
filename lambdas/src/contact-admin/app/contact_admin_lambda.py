"""
Admin API Lambda function for managing contact messages and blocked contacts.

This Lambda provides REST API endpoints for administrative operations on the
contact form system, including viewing messages, managing blocked IPs, and
retrieving system statistics.

Environment Variables:
    ALL_CONTACT_MESSAGES_TABLE_NAME: DynamoDB table for contact messages
    BLOCKED_CONTACTS_TABLE_NAME: DynamoDB table for blocked contacts
    COGNITO_USER_POOL_ID: Cognito User Pool ID for JWT validation
    COGNITO_REGION: AWS region for Cognito (default: us-west-2)
    COGNITO_APP_CLIENT_ID: Cognito App Client ID for JWT validation
"""

import json
import os
from typing import Any
import requests
from jose import jwt, JWTError
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, CORSConfig
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError
from aws_lambda_powertools.logging import correlation_paths
from pydantic import ValidationError

from models import (
    ApiResponse,
    ContactMessage,
    BlockedContact,
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

# Configure CORS to allow all origins (since this is a private admin API)
cors_config = CORSConfig(
    allow_origin="*",
    allow_headers=["Content-Type", "Authorization"],
    max_age=300,
)

app = APIGatewayHttpResolver(cors=cors_config)

# Cognito configuration
COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-west-2")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "us-west-2_YQm2Qh4B9")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID", "7ntm95jv2b3f2mfcmo81e1mavr")

# Cache for JWKS (JSON Web Key Set)
_jwks_cache = None


def get_jwks():
    """Fetch and cache the JWKS from Cognito."""
    global _jwks_cache
    if _jwks_cache is None:
        jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        logger.info(f"Fetching JWKS from {jwks_url}")
        response = requests.get(jwks_url)
        _jwks_cache = response.json()
    return _jwks_cache


def validate_jwt_token(event: dict[str, Any]) -> dict[str, Any]:
    """
    Validate JWT token from Authorization header.

    Args:
        event: API Gateway event

    Returns:
        Decoded JWT claims if valid

    Raises:
        UnauthorizedError: If token is missing or invalid
    """
    # Get Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("authorization") or headers.get("Authorization")

    if not auth_header:
        logger.warning("Missing Authorization header")
        raise UnauthorizedError("Missing Authorization header")

    # Extract token from "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Invalid Authorization header format")
        raise UnauthorizedError("Invalid Authorization header format")

    token = parts[1]

    try:
        # Get JWKS
        jwks = get_jwks()

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching key
        key = None
        for jwk_key in jwks["keys"]:
            if jwk_key["kid"] == kid:
                key = jwk_key
                break

        if not key:
            logger.warning(f"Public key not found for kid: {kid}")
            raise UnauthorizedError("Invalid token")

        # Verify and decode the token
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}",
        )

        logger.info(f"Token validated for user: {claims.get('cognito:username')}")
        return claims

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise UnauthorizedError("Invalid or expired token")
    except Exception as e:
        logger.exception(f"Unexpected error during token validation: {e}")
        raise UnauthorizedError("Token validation failed")


@app.get("/v1/contact/admin/messages")
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
        result: MessageListResponse = list_messages(
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


@app.get("/v1/contact/admin/messages/<message_id>")
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
        message: ContactMessage | None = get_message_by_id(message_id)

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


@app.get("/v1/contact/admin/stats")
def handle_get_stats() -> dict[str, Any]:
    """
    Get system statistics and analytics.

    Returns:
        200: StatsResponse with system metrics
        500: Internal server error
    """
    try:
        stats: StatsResponse = get_stats()

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


@app.get("/v1/contact/admin/blocked")
def handle_list_blocked() -> dict[str, Any]:
    """
    List all blocked contacts.

    Returns:
        200: BlockedContactListResponse with all blocked contacts
        500: Internal server error
    """
    try:
        result: BlockedContactListResponse = list_blocked_contacts()

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


@app.post("/v1/contact/admin/blocked")
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
        body: dict[str, Any] = app.current_event.json_body
        request: BlockContactRequest = BlockContactRequest(**body)

        # Block the contact
        blocked: BlockedContact = block_contact(request)

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


@app.delete("/v1/contact/admin/blocked/<blocked_id>")
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
        success: bool = unblock_contact(blocked_id)

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

    # Get HTTP method
    request_context = event.get("requestContext", {})
    http_context = request_context.get("http", {})
    method = http_context.get("method", "")

    # OPTIONS requests handled automatically by APIGatewayHttpResolver(cors=True)
    # All other requests require JWT validation
    if method != "OPTIONS":
        try:
            # Validate JWT token
            claims = validate_jwt_token(event)
            logger.info(f"Authenticated user: {claims.get('email')}")
        except UnauthorizedError as e:
            logger.warning(f"Unauthorized request: {e}")
            return {
                "statusCode": 401,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
                },
                "body": json.dumps({
                    "status": 401,
                    "error": str(e),
                    "data": None
                })
            }

    return app.resolve(event, context)
