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
        del event["queryStringParameters"]
        actual_validation_status = self._test_validator.query_params_key_present(event)

        self.assertEqual(actual_validation_status, False)  # add assertion here

    def test_missing_email_fails_validation(self):
        event = self.get_valid_event()
        # remove e-mail & expect failure
        event["queryStringParameters"].pop("user_email")

        actual_validation_status = self._test_validator.required_query_params_present(event)

        self.assertEqual(actual_validation_status, False)

    def test_missing_message_fails_validation(self):
        event = self.get_valid_event()
        # remove e-mail & expect failure
        event["queryStringParameters"].pop("user_message")

        actual_validation_status = self._test_validator.required_query_params_present(event)

        self.assertEqual(actual_validation_status, False)

    @unittest.skip("revisit test conflicts")
    def test_missing_name_does_not_fail_validation(self):
        event = self.get_valid_event()
        # remove e-mail & expect failure
        event["queryStringParameters"].pop("user_name")

        actual_validation_status = self._test_validator.required_query_params_present(event)
        self.assertEqual(actual_validation_status, False)

    def get_valid_event(self):
        return {'version': '2.0', 'routeKey': 'ANY /test/services/form/contact', 'rawPath': '/test/services/form/contact', 'rawQueryString': 'user_name=john&user_email=john%40email.com&user_message=my+message', 'headers': {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-US,en;q=0.5', 'content-length': '0', 'host': 'api.johnsosoka.com', 'referer': 'http://localhost:4000/contact/', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site', 'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0', 'x-amzn-trace-id': 'Root=1-618d6843-3a70137f1916c8915da22437', 'x-forwarded-for': '172.73.147.80', 'x-forwarded-port': '443', 'x-forwarded-proto': 'https'}, 'queryStringParameters': {'user_email': 'john@email.com', 'user_message': 'my message', 'user_name': 'john'}, 'requestContext': {'accountId': '033448470137', 'apiId': 'sjc50376aa', 'domainName': 'api.johnsosoka.com', 'domainPrefix': 'api', 'http': {'method': 'GET', 'path': '/test/services/form/contact', 'protocol': 'HTTP/1.1', 'sourceIp': '172.73.147.80', 'userAgent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'}, 'requestId': 'Ip06phMAoAMEVHw=', 'routeKey': 'ANY /test/services/form/contact', 'stage': '$default', 'time': '11/Nov/2021:19:00:19 +0000', 'timeEpoch': 1636657219983}, 'isBase64Encoded': False}


if __name__ == '__main__':
    unittest.main()
