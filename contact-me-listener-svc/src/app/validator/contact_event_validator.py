import logging
logger = logging.getLogger("app.validator.ContactEventValidator")


class ContactEventValidator:

    @staticmethod
    def validate_event(payload_event: dict) -> bool:
        is_valid = True

        if "contactEmail" not in payload_event:
            is_valid = False
            logger.warning("user_email missing from contact submission")
        if "contactMessage" not in payload_event:
            is_valid = False
            logger.warning("user_message missing from contact submission")
        if "contactName" not in payload_event:
            # Don't fail if name missing, just log it.
            logger.warning("user_name not present in contact submission...")
        return is_valid
