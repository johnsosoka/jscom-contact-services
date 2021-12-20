import logging
from app.util.body_extractor_util import BodyExtractorUtil

logger = logging.getLogger("app.validator.ContactEventValidator")


class ContactEventValidator:

    # Ensure Request Context Present?
    def validate_event_is_dict(self, event):
        pass

    def validate_event_contains_source_ip(self):
        pass

    def validate_event_contains_user_agent(self):
        pass

    def validate_request_time(self):
        pass

    @staticmethod
    def body_param_present(event: dict) -> bool:
        # aws moves query params to the body of the request & base64 encodes it.
        is_valid = True
        if "body" not in event.keys():
            logger.warning("No request body / base64 encoded query params to process.")
            is_valid = False
        return is_valid

    @staticmethod
    def required_query_params_present(decoded_body: dict) -> bool:
        is_valid = True
        params_to_validate = decoded_body.keys()

        if "user_email" not in params_to_validate:
            is_valid = False
            logger.warning("user_email missing from contact submission")
        if "user_message" not in params_to_validate:
            is_valid = False
            logger.warning("user_message missing from contact submission")
        if "user_name" not in params_to_validate:
            # Don't fail if name missing, just log it.
            logger.warning("user_name not present in contact submission...")
        return is_valid

    def validate_event(self, event):
        if not self.body_param_present(event):
            return False

        sanitized_dict = BodyExtractorUtil.decode_body_params_to_dict(event["body"])

        required_param_fields_present = self.required_query_params_present(sanitized_dict)

        return required_param_fields_present
