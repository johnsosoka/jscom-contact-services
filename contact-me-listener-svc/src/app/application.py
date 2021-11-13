import logging
from app.common.constants import (TOPIC_ARN_KEY,
                                  VALIDATION_FAILURE_MESSAGE,
                                  FAILURE_EXECUTION,
                                  PUBLISH_FAILURE_MESSAGE,
                                  SUCCESS_EXECUTION,
                                  PUBLISH_SUCCESS_MESSAGE,
                                  GENERIC_FAILURE_MESSAGE
                                  )
from app.validator.contact_event_validator import ContactEventValidator
from app.mapper.contact_event_mapper import ContactEventMapper
from app.publisher.sns_publisher import SNSPublisher
import json
import os

logger = logging.getLogger("app.Application")


class Application:

    def __init__(self):
        self._contact_event_validator = ContactEventValidator()
        self._sns_publisher = SNSPublisher()

    def run(self, event):
        """Handle form submit event

        process, validate & submit event to SNS.
        :param event:
        :return:
        """
        # Validate Event
        is_event_valid = self._contact_event_validator.validate_event(event)

        if is_event_valid is False:
            logger.warning("Validation failure, preparing failure response.")
            return self.prepare_message(400, FAILURE_EXECUTION, VALIDATION_FAILURE_MESSAGE)

        # Map Relevant Fields to Contact Me Submission Model
        contact_me_submission = ContactEventMapper.map_event_to_contact_model(event)
        topic_arn = os.environ.get(TOPIC_ARN_KEY)

        if topic_arn is None:
            logger.error("ARN Does not appear to be set for env property {}".format(TOPIC_ARN_KEY))
            return self.prepare_message(500, FAILURE_EXECUTION, GENERIC_FAILURE_MESSAGE)

        # Publish
        try:
            self._sns_publisher.publish_message(topic_arn, contact_me_submission.to_json())
        except Exception as e:
            logger.error("Exception publishing to topic_arn {}".format(topic_arn), e)
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
