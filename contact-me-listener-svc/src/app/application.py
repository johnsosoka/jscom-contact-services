import logging
from app.common.constants import (TOPIC_ARN_KEY,
                                  VALIDATION_FAILURE_MESSAGE,
                                  FAILURE_EXECUTION,
                                  PUBLISH_FAILURE_MESSAGE,
                                  SUCCESS_EXECUTION,
                                  PUBLISH_SUCCESS_MESSAGE
                                  )
from app.validator.contact_event_validator import ContactEventValidator
from app.publisher.sns_publisher import SNSPublisher
from app.util.event_processing_util import EventProcessingUtil
import json
import os

logger = logging.getLogger("app.Application")
logger.setLevel(logging.DEBUG)


class Application:

    def __init__(self):
        self._contact_event_validator = ContactEventValidator()
        self._sns_publisher = SNSPublisher()
        self._topic_arn = os.environ.get(TOPIC_ARN_KEY)

    def handle(self, event):
        """Handle form submit event

        process, validate & submit event to SNS.
        :param: event
        :return:
        """
        logger.debug("handling event {}".format(str(event)))

        contact_event = EventProcessingUtil.extract_relevant_fields(event)

        # Validate Event
        valid_event = self._contact_event_validator.validate_event(contact_event)

        if not valid_event:
            logger.warning("Validation failure, preparing failure response.")
            return self.prepare_message(400, FAILURE_EXECUTION, VALIDATION_FAILURE_MESSAGE)

        try:
            self._sns_publisher.publish_message(self._topic_arn, json.dumps(contact_event))
        except Exception as e:
            logger.error("Exception publishing to topic_arn {arn}".format(arn=self._topic_arn))
            logger.error(e)
            return self.prepare_message(500, FAILURE_EXECUTION, PUBLISH_FAILURE_MESSAGE)

        return self.prepare_message(200, SUCCESS_EXECUTION, PUBLISH_SUCCESS_MESSAGE)

    @staticmethod
    def prepare_message(status_code: int, execution_status, message="none"):
        response_body = {"execution_status": execution_status,
                         "message:": message}

        return {
            'statusCode': status_code,
            'body': json.dumps(response_body)
        }
