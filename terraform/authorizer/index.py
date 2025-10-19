"""
Lambda authorizer for API Gateway v2 HTTP API.

This authorizer validates the x-api-key header against a configured API key
stored in the ADMIN_API_KEY environment variable.

Returns simple boolean responses for API Gateway v2:
- {"isAuthorized": true} for valid API keys
- {"isAuthorized": false} for invalid or missing API keys
"""

import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda authorizer handler for API Gateway v2.

    Args:
        event: API Gateway v2 authorizer event with format version 2.0
        context: Lambda context object

    Returns:
        Simple authorization response:
        - {"isAuthorized": true} if API key is valid
        - {"isAuthorized": false} otherwise
    """
    logger.info(f"Authorizer invoked for request: {event.get('requestContext', {}).get('requestId')}")

    # Get the expected API key from environment
    expected_api_key = os.environ.get("ADMIN_API_KEY")

    if not expected_api_key:
        logger.error("ADMIN_API_KEY environment variable not set")
        return {"isAuthorized": False}

    # Extract x-api-key header from event
    # API Gateway v2 format: event['headers']['x-api-key']
    headers = event.get("headers", {})

    # Header names are lowercase in API Gateway v2
    provided_api_key = headers.get("x-api-key")

    if not provided_api_key:
        logger.warning("No x-api-key header provided")
        return {"isAuthorized": False}

    # Validate the API key
    if provided_api_key == expected_api_key:
        logger.info("API key validated successfully")
        return {"isAuthorized": True}
    else:
        logger.warning("Invalid API key provided")
        return {"isAuthorized": False}
