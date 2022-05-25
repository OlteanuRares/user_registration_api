import json

from django.test import TestCase

from src.api.decorators import jsonify


@jsonify
def dummy_view(*args, **kwargs):
    return {'asdf': 'zxcv'}


class TestJsonify(TestCase):

    def test_ok_status_code(self):
        """If the view returns successfully, a 200 status code is returned
        """
        response = dummy_view()
        self.assertEqual(response.status_code, 200, 'Invalid status code')

    def test_content_type_set(self):
        """The `content-type` header should be set
        """
        response = dummy_view()
        self.assertTrue('Content-Type' in response,
                        'The content-type header was not set')

    def test_content_type_json(self):
        """The `content-type` header should be set to `application/json`
        """
        response = dummy_view()
        self.assertEqual(response['Content-Type'], 'application/json',
                         "Wrong content type of the response")

    def test_content_json(self):
        """The actual content type returned by @jsonify is indeed JSON
        """
        response = dummy_view()
        try:
            json.loads(response.content)
        except ValueError as err:
            self.fail(err.message)

    def test_raises_custom_500_on_error(self):
        """Any unknown exception raised in the view appear as 500 server error
        """

        @jsonify
        def raises_exception(*args, **kwargs):
            raise Exception()

        response = raises_exception()
        self.assertEqual(response.status_code, 500)
        response_dict = json.loads(response.content)
        self.assertEqual(response_dict, {"errors": ["Internal server error"]})
