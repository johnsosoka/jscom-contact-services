import json


class ContactMeSubmission:
    """Encapsulates Contact Me Submissions

    Additionally provides helper functions to dump encapsulated data to json & strip private field indicators
    """

    def __init__(self):
        self._contact_name = ''
        self._contact_email = ''
        self._contact_message = ''

    @property
    def contact_name(self) -> str:
        return self._contact_name

    @contact_name.setter
    def contact_name(self, contact_name) -> None:
        self._contact_name = contact_name

    @property
    def contact_email(self) -> str:
        return self._contact_email

    @contact_email.setter
    def contact_email(self, contact_email) -> None:
        self._contact_email = contact_email

    @property
    def contact_message(self) -> str:
        return self._contact_message

    @contact_message.setter
    def contact_message(self, contact_message) -> None:
        self._contact_message = contact_message

    def to_json(self) -> str:
        my_dict = self.__dict__
        return json.dumps(self.remove_private_field_indicators(my_dict))

    @staticmethod
    def remove_private_field_indicators(dict_to_convert: dict):
        """Helper method to strip python private field indicators

        Method to strip `_` private field indicator from top level dict keys.

        :param dict_to_convert:
        :return:
        """
        for key in dict_to_convert.keys():
            new_key = key[1:]  # strip first character of original key
            dict_to_convert[new_key] = dict_to_convert.pop(key)  # swap replace old value with new value
        return dict_to_convert
