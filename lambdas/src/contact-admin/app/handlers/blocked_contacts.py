"""
Blocked contact operation handlers for the admin API.

Provides functions for managing the blocked contacts list.
"""

import os
import boto3
import uuid
from aws_lambda_powertools import Logger
from models import BlockedContact, BlockedContactListResponse, BlockContactRequest
from utils import item_to_blocked_contact, blocked_contact_to_item

logger = Logger()

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
blocked_table_name = os.environ['BLOCKED_CONTACTS_TABLE_NAME']
blocked_table = dynamodb.Table(blocked_table_name)


def list_blocked_contacts() -> BlockedContactListResponse:
    """
    List all blocked contacts.

    Returns:
        BlockedContactListResponse containing all blocked contacts

    Raises:
        Exception: If DynamoDB query fails
    """
    logger.info("Listing all blocked contacts")

    try:
        response = blocked_table.scan()
        blocked_contacts = [
            item_to_blocked_contact(item)
            for item in response.get('Items', [])
        ]

        # Handle pagination if there are more results
        while 'LastEvaluatedKey' in response:
            response = blocked_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            blocked_contacts.extend([
                item_to_blocked_contact(item)
                for item in response.get('Items', [])
            ])

        logger.info(f"Retrieved {len(blocked_contacts)} blocked contacts")

        return BlockedContactListResponse(
            blocked_contacts=blocked_contacts,
            count=len(blocked_contacts)
        )

    except Exception as e:
        logger.error(f"Error listing blocked contacts: {e}")
        raise


def block_contact(request: BlockContactRequest) -> BlockedContact:
    """
    Add an IP address to the blocked contacts list.

    Args:
        request: BlockContactRequest containing IP address and user agent

    Returns:
        BlockedContact representing the newly created block

    Raises:
        ValueError: If IP address is already blocked
        Exception: If DynamoDB operation fails
    """
    logger.info(f"Blocking contact: {request.ip_address}")

    try:
        # Check if IP is already blocked
        response = blocked_table.scan(
            FilterExpression='ip_address = :ip',
            ExpressionAttributeValues={':ip': request.ip_address}
        )

        if response.get('Items'):
            logger.warning(f"IP already blocked: {request.ip_address}")
            raise ValueError(f"IP address {request.ip_address} is already blocked")

        # Create new blocked contact
        blocked_contact = BlockedContact(
            id=str(uuid.uuid4()),
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            is_blocked=1
        )

        # Write to DynamoDB
        item = blocked_contact_to_item(blocked_contact)
        blocked_table.put_item(Item=item)

        logger.info(f"Successfully blocked contact: {request.ip_address}")

        return blocked_contact

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error blocking contact: {e}")
        raise


def unblock_contact(blocked_id: str) -> bool:
    """
    Remove a blocked contact entry by ID.

    Args:
        blocked_id: The ID of the blocked contact record to remove

    Returns:
        True if successfully deleted, False if not found

    Raises:
        Exception: If DynamoDB operation fails
    """
    logger.info(f"Unblocking contact: {blocked_id}")

    try:
        # Check if the record exists
        response = blocked_table.get_item(Key={'id': blocked_id})

        if 'Item' not in response:
            logger.info(f"Blocked contact not found: {blocked_id}")
            return False

        # Delete the record
        blocked_table.delete_item(Key={'id': blocked_id})

        logger.info(f"Successfully unblocked contact: {blocked_id}")

        return True

    except Exception as e:
        logger.error(f"Error unblocking contact: {e}")
        raise
