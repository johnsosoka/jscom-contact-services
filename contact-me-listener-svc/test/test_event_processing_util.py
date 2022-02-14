import unittest

from src.app.util.event_processing_util import EventProcessingUtil
from json import JSONDecodeError

class TestEventProcessingUtil(unittest.TestCase):

    def setUp(self) -> None:
        self.event_processing_util = EventProcessingUtil()
        self.valid_base64_encoded_string = \
            "eyJjb250YWN0TmFtZSI6ImpvaG4iLCJjb250YWN0RW1haWwiOiJqb2h" + \
            "uQHRlc3QuY29tIiwiY29udGFjdE1lc3NhZ2UiOiJ0ZXN0IG1lc3NhZ2UifQ=="
        self.test_event = {
            'version': '2.0',
            'routeKey': 'POST /services/form/contact',
            'rawPath': '/services/form/contact',
            'rawQueryString': '',
            'headers': {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'content-length': '85',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'host': 'api.johnsosoka.com',
                'origin': 'http://localhost:4000',
                'referer': 'http://localhost:4000/',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15' +
                              '(KHTML, like Gecko) Version/15.3 Safari/605.1.15',
                'x-amzn-trace-id': 'Root=1-62097b36-486a181638d037d5090a342f',
                'x-forwarded-for': '152.73.127.80',
                'x-forwarded-port': '443',
                'x-forwarded-proto': 'https'
            },
            'requestContext': {
                'accountId': '033448470137',
                'apiId': 'k6mta3dh76',
                'domainName': 'api.johnsosoka.com',
                'domainPrefix': 'api',
                'http': {
                    'method': 'POST',
                    'path': '/services/form/contact',
                    'protocol': 'HTTP/1.1',
                    'sourceIp': '152.73.127.80',
                    'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15' +
                                 '(KHTML, like Gecko) Version/15.3 Safari/605.1.15'
                },
                'requestId': 'NgAwjik1IAMEMeA=',
                'routeKey': 'POST /services/form/contact',
                'stage': '$default',
                'time': '13/Feb/2022:21:42:14 +0000',
                'timeEpoch': 1644788534516
            },
            'body': 'eyJjb250YWN0TmFtZSI6ImpvaG4iLCJjb250YWN0RW1haWwiOiJqb2huQHRlc3QuY29tIiwiY29udGFjdE1l' +
                    'c3NhZ2UiOiJ0ZXN0IG1lc3NhZ2UifQ==',
            'isBase64Encoded': True
        }

    def test_decode_method_can_decode_valid_message_to_dict(self):
        decoded_response = self.event_processing_util._decode_body_to_dict(self.valid_base64_encoded_string)
        self.assertTrue(isinstance(decoded_response, dict))

    def test_decode_method_empty_body_throws_error(self):
        error_thrown = False
        with self.assertRaises(JSONDecodeError):
            decoded_response = self.event_processing_util._decode_body_to_dict("")

    def test_decode_method_bad_base54_throws_error(self):
        with self.assertRaises(Exception):
            decoded_response = self.event_processing_util._decode_body_to_dict("BADBASE64STRING")

    def test_event_util_extracts_and_merges_fields(self):
        result = self.event_processing_util.extract_relevant_fields(self.test_event)
        print(result)
        self.assertEqual(self.test_event["requestContext"]['http']['sourceIp'], result['sourceIP'])
        self.assertEqual(self.test_event["requestContext"]['http']['userAgent'], result['userAgent'])
        self.assertEqual("john", result['contactName'])
        self.assertEqual("john@test.com", result["contactEmail"])
        self.assertEqual("test message", result["contactMessage"])

if __name__ == '__main__':
    unittest.main()
