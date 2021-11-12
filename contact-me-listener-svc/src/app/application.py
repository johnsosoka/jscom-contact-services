from app.validator.contact_event_validator import ContactEventValidator
from app.mapper.contact_event_mapper import ContactEventMapper


class Application:

    def __init__(self):
        self._contact_event_validator = ContactEventValidator()

    def run(self, event):
        """Handle form submit event

        process, validate & submit event to SNS.
        :param event:
        :return:
        """
        # Validate Event
        is_event_valid = self._contact_event_validator.validate_event(event)

        if is_event_valid is False:
            print("Failed validation.")
            return "TODO FAILURE MESSAGE"

        # Map Relevant Fields to Contact Me Submission Model
        contact_me_submission = ContactEventMapper.map_event_to_contact_model(event)

        # Publish

        pass
