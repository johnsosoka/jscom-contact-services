from app.common.constants import FIELD_QUERY_STRING_PARAMS, FIELD_USER_NAME, FIELD_USER_EMAIL, FIELD_USER_MESSAGE
from src.app.mapper.contact_event_mapper import ContactEventMapper
import test_data
import unittest

# base64 test event: dXNlcl9uYW1lPW9uZSZ1c2VyX2VtYWlsPXR3byU0MHRocmVlLmNvbSZ1c2VyX21lc3NhZ2U9Zm91cg==
# base64 decoded event: user_name=one&user_email=two%40three.com&user_message=four

class TestContactEventMapper(unittest.TestCase):

    def setUp(self) -> None:
        self._validator = ContactEventMapper()

    def test_can_map_user_name(self):
        test_event = test_data.example_event_dict.copy()

        expected_name = "one"
        mapped_data = self._validator.map_event_to_contact_model(test_event)

        self.assertEqual(expected_name, mapped_data.contact_name)

    def test_can_map_user_mail(self):
        test_event = test_data.example_event_dict.copy()

        expected_mail = "two@three.com"
        mapped_data = self._validator.map_event_to_contact_model(test_event)

        self.assertEqual(expected_mail, mapped_data.contact_email)

    def test_can_map_user_message(self):
        test_event = test_data.example_event_dict.copy()

        expected_message = "four"
        mapped_data = self._validator.map_event_to_contact_model(test_event)

        self.assertEqual(expected_message, mapped_data.contact_message)

    @unittest.skip("revisit when manipulating encoded event")
    def test_can_map_with_missing_name(self):
        test_event = test_data.example_event_dict.copy()

        # remove name field (it's not mandatory)
        del test_event[FIELD_QUERY_STRING_PARAMS][FIELD_USER_NAME]

        expected_mail = test_event[FIELD_QUERY_STRING_PARAMS][FIELD_USER_EMAIL]
        expected_message = test_event[FIELD_QUERY_STRING_PARAMS][FIELD_USER_MESSAGE]
        mapped_data = self._validator.map_event_to_contact_model(test_event)

        self.assertEqual(expected_mail, mapped_data.contact_email)
        self.assertEqual(expected_message, mapped_data.contact_message)




if __name__ == '__main__':
    unittest.main()
