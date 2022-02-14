import base64
import json


class EventProcessingUtil:

    @staticmethod
    def extract_relevant_fields(event):
        """
        Extracts request body, decodes if necessary & combines with contact identifiers from the EventContext
        :param event:
        :return:
        """
        event_body = EventProcessingUtil._extract_request_body(event)
        identifiers = EventProcessingUtil._extract_request_identifiers(event)

        # combine dictionaries
        event_body.update(identifiers)
        return event_body

    @staticmethod
    def _decode_body_to_dict(base64_encoded_body) -> dict:
        decoded_body = base64.b64decode(base64_encoded_body).decode("utf-8")
        return json.loads(decoded_body)

    @staticmethod
    def _extract_request_body(event) -> dict:
        """
        Extracts request body, base64 decodes if necessary and returns a dictionary.

        :param: event
        :return: dict
        """
        event_body = ""
        if event["isBase64Encoded"]:
            event_body = EventProcessingUtil._decode_body_to_dict(event["body"])
        else:
            event_body = json.loads(event["body"])

        return event_body

    @staticmethod
    def _extract_request_identifiers(event):
        """
        Method to fetch fields which could aid a spam filter.
        :param: event
        :return:
        """
        request_identifiers = {"userAgent": event["requestContext"]["http"]["userAgent"],
                              "sourceIP": event["requestContext"]["http"]["sourceIp"]}

        return request_identifiers
