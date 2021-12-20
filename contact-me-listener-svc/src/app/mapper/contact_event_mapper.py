from app.common.constants import FIELD_QUERY_STRING_PARAMS, FIELD_USER_MESSAGE, FIELD_USER_EMAIL, FIELD_USER_NAME
from app.model.contact_me_submission import ContactMeSubmission
from app.util.body_extractor_util import BodyExtractorUtil


class ContactEventMapper:

    @staticmethod
    def map_event_to_contact_model(event: dict) -> ContactMeSubmission:

        mapped_model = ContactMeSubmission()
        body = event["body"]
        relevant_event_params = BodyExtractorUtil().decode_body_params_to_dict(body)

        mapped_model.contact_email = relevant_event_params[FIELD_USER_EMAIL]
        mapped_model.contact_message = relevant_event_params[FIELD_USER_MESSAGE]

        # Check before reading non mandatory field
        if FIELD_USER_NAME in relevant_event_params.keys():
            mapped_model.contact_name = relevant_event_params[FIELD_USER_NAME]

        return mapped_model

