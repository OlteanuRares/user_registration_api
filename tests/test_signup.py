import logging
from django.urls import reverse
from django.test import TestCase, Client

from src.api.utils import delete_api_user
from src.api.models import ApiUser


LOGGER = logging.getLogger(__name__)


class TestSignUp(TestCase):
    logger = 'src.api.views'

    def setUp(self):
        self.url = reverse('api.sign_up')
        self.client = Client()
        self.api_user = ApiUser.objects.create(
            email="foo@bar.com",
            password="baz"
        )

    def tearDown(self):
        delete_api_user(email=self.api_user.email)

    def test_sign_up_not_accepted_method(self):
        for method in ['get', 'patch', 'put', 'delete']:
            response = getattr(self.client, method)(self.url)
            content = response.json()
            assert response.status_code == 405
            assert content.get('errors') == 'Method not allowed'

    def test_post_invalid_content_type(self):
        for content_type in ['application/octet-stream', 'text/plain', 'application/xml']:
            response = self.client.post(
               self.url,
                data={"email": "foo", "password": "bar"},
                content_type=content_type
            )
            content = response.json()
            assert response.status_code == 415
            assert content.get('errors') == 'Invalid content type'

    def test_post_with_missing_data(self):
        response = self.client.post(
            self.url,
            data={"email": "foo"},
            content_type='application/json'
        )
        content = response.json()
        assert response.status_code == 403
        assert content.get('errors') == 'Email, and password should be sent in the request body.'

        response = self.client.post(
            self.url,
            data={"password": "foo"},
            content_type='application/json'
        )
        content = response.json()
        assert response.status_code == 403
        assert content.get('errors') == 'Email, and password should be sent in the request body.'

    def test_post_new_user(self):
        with self.assertLogs(logger=self.logger, level='INFO') as lg:
            lg._replace(output=[])
            response = self.client.post(
                self.url,
                data={
                    "email": "foo@bar.com",
                    "password": "baz"
                },
                content_type='application/json'
            )

            self.assertIn("Activation mail sent to foo@bar.com.", ','.join(lg.output))
        assert response.status_code == 201
        content = response.json()
        assert "Activation mail sent to foo@bar.com." in content['message']
