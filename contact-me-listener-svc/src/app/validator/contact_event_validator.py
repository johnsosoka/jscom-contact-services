import logging
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
    def query_params_key_present(event: dict) -> bool:
        # params exist
        is_valid = True
        if "queryStringParameters" not in event.keys():
            logger.warning("query string parameters not present in request.")
            is_valid = False
        return is_valid

    @staticmethod
    def required_query_params_present(event: dict) -> bool:
        is_valid = True
        params_to_validate = event["queryStringParameters"].keys()

        if "user_email" not in event["queryStringParameters"].keys():
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
        params_key_exist = self.query_params_key_present(event)

        if not params_key_exist:
            return False

        required_param_fields_present = self.required_query_params_present(event)

        return required_param_fields_present
