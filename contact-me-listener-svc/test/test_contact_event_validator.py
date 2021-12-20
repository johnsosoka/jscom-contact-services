import unittest

from app.validator.contact_event_validator import ContactEventValidator


class TestContactMeEventValidator(unittest.TestCase):

    def setUp(self) -> None:
        self._test_validator = ContactEventValidator()

    def test_valid_event_passes_validation(self):
        event = self.get_valid_event()

        actual_validation_status = self._test_validator.validate_event(event)
        self.assertEqual(actual_validation_status, True)

    def test_missing_query_params_fails_validation(self):
        # remove required key & test
        event = self.get_valid_event()
        del event["body"]
        actual_validation_status = self._test_validator.body_param_present(event)

        self.assertEqual(actual_validation_status, False)  # add assertion here

    def test_missing_email_fails_validation(self):
        body = self.get_valid_decoded_body()

        body.pop("user_email")

        actual_validation_status = self._test_validator.required_query_params_present(body)

        self.assertEqual(actual_validation_status, False)

    def test_missing_message_fails_validation(self):
        body = self.get_valid_decoded_body()
        # remove e-mail & expect failure
        body.pop("user_message")

        actual_validation_status = self._test_validator.required_query_params_present(body)

        self.assertEqual(actual_validation_status, False)

    def test_missing_name_does_not_fail_validation(self):
        body = self.get_valid_decoded_body()
        # remove e-mail & expect failure
        body.pop("user_name")

        actual_validation_status = self._test_validator.required_query_params_present(body)
        self.assertEqual(actual_validation_status, True)

    @staticmethod
    def get_valid_decoded_body():
        return {'user_name': 'one', 'user_email': 'two@three.com', 'user_message': 'four'}

    @staticmethod
    def get_valid_event():
        return {'version': '2.0', 'routeKey': 'POST /services/form/contact', 'rawPath': '/services/form/contact', 'rawQueryString': '', 'headers': {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-US,en;q=0.5', 'content-length': '58', 'content-type': 'application/x-www-form-urlencoded', 'host': 'k6mta3dh76.execute-api.us-east-1.amazonaws.com', 'origin': 'http://localhost:4000', 'referer': 'http://localhost:4000/contact/', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site', 'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0', 'x-amzn-trace-id': 'Root=1-61ab821b-1d308c9d55513cab60dec0cd', 'x-forwarded-for': '172.73.147.80', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'requestContext': {'accountId': '033448470137', 'apiId': 'k6mta3dh76', 'domainName': 'k6mta3dh76.execute-api.us-east-1.amazonaws.com', 'domainPrefix': 'k6mta3dh76', 'http': {'method': 'POST', 'path': '/services/form/contact', 'protocol': 'HTTP/1.1', 'sourceIp': '172.73.147.80', 'userAgent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'}, 'requestId': 'J1FEXjVvoAMEMsw=', 'routeKey': 'POST /services/form/contact', 'stage': '$default', 'time': '04/Dec/2021:14:58:35 +0000', 'timeEpoch': 1638629915770}, 'body': 'dXNlcl9uYW1lPW9uZSZ1c2VyX2VtYWlsPXR3byU0MHRocmVlLmNvbSZ1c2VyX21lc3NhZ2U9Zm91cg==', 'isBase64Encoded': True}


if __name__ == '__main__':
    unittest.main()
