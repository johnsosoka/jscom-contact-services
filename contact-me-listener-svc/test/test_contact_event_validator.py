import unittest

from app.validator.contact_event_validator import ContactEventValidator


class TestContactMeEventValidator(unittest.TestCase):

    def setUp(self) -> None:
        self._test_validator = ContactEventValidator()
        self._valid_event = {'contactName': 'john',
                             'contactEmail': 'john@test.com',
                             'contactMessage': 'test message',
                             'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ' +
                                          'AppleWebKit/605.1.15(KHTML, like Gecko) Version/15.3 Safari/605.1.15',
                             'sourceIP': '152.73.127.80'}


    def test_valid_event_passes_validation(self):
        event = self.get_valid_event()

        actual_validation_status = self._test_validator.validate_event(event)
        self.assertEqual(actual_validation_status, True)


    def test_missing_email_fails_validation(self):
        event = self.get_valid_event()

        # remove e-mail & expect failure
        event.pop("contactEmail")

        actual_validation_status = self._test_validator.validate_event(event)

        self.assertEqual(actual_validation_status, False)

    def test_missing_message_fails_validation(self):
        event = self.get_valid_event()

        # remove message & expect failure
        event.pop("contactMessage")

        actual_validation_status = self._test_validator.validate_event(event)

        self.assertEqual(actual_validation_status, False)

    def test_missing_name_does_not_fail_validation(self):
        event = self.get_valid_event()

        # remove contact name & expect success
        event.pop("contactName")

        actual_validation_status = self._test_validator.validate_event(event)
        self.assertEqual(actual_validation_status, True)

    @staticmethod
    def get_valid_event():
        return {'contactName': 'john',
                'contactEmail': 'john@test.com',
                'contactMessage': 'test message',
                'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ' +
                             'AppleWebKit/605.1.15(KHTML, like Gecko) Version/15.3 Safari/605.1.15',
                'sourceIP': '152.73.127.80'}

if __name__ == '__main__':
    unittest.main()
