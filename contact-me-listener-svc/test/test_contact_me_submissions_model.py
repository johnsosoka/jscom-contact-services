import unittest
from src.app.model.contact_me_submission import ContactMeSubmission


class TestContactMeSubmissionsModel(unittest.TestCase):
    """Tests for ContactMeSUbmissionModel

    * only testing helper methods
    * intentionally not testing getters/setters.
    """

    def test_can_convert_object_to_json(self):
        expected_json_output = '{"contact_name": "john", "contact_email": "contact@email.com", "contact_message": "you got something wrong..."}'
        # prepare test object
        test_contact_submission = ContactMeSubmission()
        test_contact_submission.contact_name = 'john'
        test_contact_submission.contact_email = 'contact@email.com'
        test_contact_submission.contact_message = 'you got something wrong...'

        actual_json_string = test_contact_submission.to_json()

        self.assertEqual(expected_json_output, actual_json_string)


if __name__ == '__main__':
    unittest.main()
