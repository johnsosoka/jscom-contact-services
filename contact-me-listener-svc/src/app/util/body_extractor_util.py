import base64
from urllib.parse import parse_qs


class BodyExtractorUtil:

    @staticmethod
    def decode_body_params_to_dict(base64_encoded_body) -> dict:
        decoded_body = base64.b64decode(base64_encoded_body).decode("utf-8")
        dict_decoded = parse_qs(decoded_body)
        if type(dict_decoded) == dict:
            return {k: v[0] for k, v in dict_decoded.items()}
