"""
Message operation handlers for the admin API.

Provides functions for listing, retrieving, and analyzing contact messages.
"""

import os
import boto3
import base64
import json
import time
from typing import Any
from aws_lambda_powertools import Logger
from models import ContactMessage, MessageListResponse, StatsResponse
from utils import item_to_contact_message

logger = Logger()

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
messages_table_name = os.environ['ALL_CONTACT_MESSAGES_TABLE_NAME']
messages_table = dynamodb.Table(messages_table_name)


def list_messages(
    limit: int = 50,
    next_token: str | None = None,
    contact_type: str | None = None
) -> MessageListResponse:
    """
    List contact messages with pagination and optional filtering.

    Args:
        limit: Maximum number of messages to return (1-100)
        next_token: Pagination token for retrieving next page
        contact_type: Optional filter by contact type ('standard' or 'consulting')

    Returns:
        MessageListResponse containing messages and pagination info

    Raises:
        Exception: If DynamoDB query fails
    """
    logger.info(f"Listing messages: limit={limit}, next_token={next_token}, contact_type={contact_type}")

    try:
        scan_kwargs: dict[str, Any] = {
            'Limit': limit,
        }

        # Add filter expression if contact_type is specified
        if contact_type:
            scan_kwargs['FilterExpression'] = 'contact_type = :contact_type'
            scan_kwargs['ExpressionAttributeValues'] = {':contact_type': contact_type}

        # Add pagination token if provided
        if next_token:
            try:
                decoded_token = json.loads(base64.b64decode(next_token).decode('utf-8'))
                scan_kwargs['ExclusiveStartKey'] = decoded_token
            except Exception as e:
                logger.error(f"Failed to decode pagination token: {e}")
                raise ValueError("Invalid pagination token")

        response = messages_table.scan(**scan_kwargs)

        # Convert DynamoDB items to domain models
        messages = [item_to_contact_message(item) for item in response.get('Items', [])]

        # Sort by timestamp descending (most recent first)
        messages.sort(key=lambda x: x.timestamp, reverse=True)

        # Encode pagination token if more results available
        encoded_next_token = None
        if 'LastEvaluatedKey' in response:
            token_bytes = json.dumps(response['LastEvaluatedKey']).encode('utf-8')
            encoded_next_token = base64.b64encode(token_bytes).decode('utf-8')

        logger.info(f"Retrieved {len(messages)} messages")

        return MessageListResponse(
            messages=messages,
            next_token=encoded_next_token,
            count=len(messages)
        )

    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise


def get_message_by_id(message_id: str) -> ContactMessage | None:
    """
    Retrieve a specific contact message by ID.

    Args:
        message_id: The unique message identifier

    Returns:
        ContactMessage if found, None otherwise

    Raises:
        Exception: If DynamoDB query fails
    """
    logger.info(f"Retrieving message: {message_id}")

    try:
        response = messages_table.get_item(Key={'id': message_id})

        if 'Item' not in response:
            logger.info(f"Message not found: {message_id}")
            return None

        message = item_to_contact_message(response['Item'])
        logger.info(f"Successfully retrieved message: {message_id}")

        return message

    except Exception as e:
        logger.error(f"Error retrieving message: {e}")
        raise


def get_stats() -> StatsResponse:
    """
    Calculate and return statistics about the contact system.

    Computes metrics including total messages, blocked counts, and recent activity.

    Returns:
        StatsResponse containing system statistics

    Raises:
        Exception: If DynamoDB queries fail
    """
    logger.info("Calculating system statistics")

    try:
        # Get blocked contacts table
        blocked_table_name = os.environ['BLOCKED_CONTACTS_TABLE_NAME']
        blocked_table = dynamodb.Table(blocked_table_name)

        # Scan all messages
        messages_response = messages_table.scan()
        all_messages = messages_response['Items']

        # Handle pagination if there are more messages
        while 'LastEvaluatedKey' in messages_response:
            messages_response = messages_table.scan(
                ExclusiveStartKey=messages_response['LastEvaluatedKey']
            )
            all_messages.extend(messages_response['Items'])

        # Scan all blocked contacts
        blocked_response = blocked_table.scan()
        blocked_contacts = blocked_response['Items']

        # Handle pagination for blocked contacts
        while 'LastEvaluatedKey' in blocked_response:
            blocked_response = blocked_table.scan(
                ExclusiveStartKey=blocked_response['LastEvaluatedKey']
            )
            blocked_contacts.extend(blocked_response['Items'])

        # Calculate statistics
        total_messages = len(all_messages)
        blocked_count = sum(1 for msg in all_messages if int(msg.get('is_blocked', 0)) == 1)
        unblocked_count = total_messages - blocked_count
        total_blocked_ips = len(blocked_contacts)

        # Calculate recent messages (last 24 hours)
        current_time = int(time.time())
        twenty_four_hours_ago = current_time - (24 * 60 * 60)
        recent_messages_24h = sum(
            1 for msg in all_messages
            if int(msg.get('timestamp', 0)) >= twenty_four_hours_ago
        )

        # Count by contact type
        consulting_messages = sum(
            1 for msg in all_messages
            if msg.get('contact_type', 'standard') == 'consulting'
        )
        standard_messages = sum(
            1 for msg in all_messages
            if msg.get('contact_type', 'standard') == 'standard'
        )

        stats = StatsResponse(
            total_messages=total_messages,
            blocked_count=blocked_count,
            unblocked_count=unblocked_count,
            total_blocked_ips=total_blocked_ips,
            recent_messages_24h=recent_messages_24h,
            consulting_messages=consulting_messages,
            standard_messages=standard_messages,
        )

        logger.info(f"Stats calculated: {stats.model_dump()}")

        return stats

    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise
