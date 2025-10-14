import json
import boto3
import os
import logging
from notification_methods import EmailNotificationMethod

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get queue URL from environment variable
queue_url = os.environ['CONTACT_NOTIFY_QUEUE']

# Initialize notification methods
NOTIFICATION_METHODS = [
    EmailNotificationMethod(),
    # Future methods can be added here:
    # DiscordNotificationMethod(),
    # SlackNotificationMethod(),
]


def lambda_handler(event, context):
    """
    Process contact notifications by sending through all enabled notification methods.

    This lambda orchestrates sending notifications via multiple channels (email, Discord, etc.).
    Only deletes the SQS message if ALL enabled notification methods succeed.
    """
    # Get the message from the event
    message = event['Records'][0]['body']

    # Parse the message body
    message_body = json.loads(message)

    # Validate the required field
    contact_message = message_body.get('contact_message')
    if not contact_message:
        logger.error("Missing required field: contact_message")
        return {
            'statusCode': 400,
            'body': 'Missing required field: contact_message'
        }

    # Filter to only enabled notification methods
    enabled_methods = [method for method in NOTIFICATION_METHODS if method.is_enabled()]

    if not enabled_methods:
        logger.warning("No notification methods are enabled")
        return {
            'statusCode': 200,
            'body': 'No notification methods enabled'
        }

    logger.info(f"Processing notification with {len(enabled_methods)} enabled method(s)")

    # Send notification via all enabled methods
    results = {}
    all_successful = True

    for method in enabled_methods:
        method_name = method.get_method_name()
        logger.info(f"Sending notification via {method_name}")

        try:
            result = method.send_notification(message_body)
            results[method_name] = result

            if not result.get('success', False):
                all_successful = False
                logger.error(f"{method_name} notification failed: {result.get('error', 'Unknown error')}")
            else:
                logger.info(f"{method_name} notification sent successfully")

        except Exception as e:
            all_successful = False
            logger.error(f"Exception sending {method_name} notification: {str(e)}")
            results[method_name] = {
                'success': False,
                'error': str(e)
            }

    # Only delete the message from the queue if ALL methods succeeded
    if all_successful:
        sqs = boto3.client('sqs')
        receipt_handle = event['Records'][0]['receiptHandle']
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        logger.info("All notifications sent successfully, message deleted from queue")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'All notifications sent successfully',
                'results': results
            })
        }
    else:
        logger.error("One or more notifications failed, message will remain in queue for retry")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'One or more notification methods failed',
                'results': results
            })
        }
