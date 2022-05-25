import logging
import base64

from dateutil.relativedelta import relativedelta

from django.urls import reverse
from django.test import TestCase, Client
from django.utils import timezone

from src.api.models import ApiUser
from src.api.utils import insert_api_user, save_token, get_api_user, delete_api_user


LOGGER = logging.getLogger(__name__)


class TestActivation(TestCase):
    logger = 'src.api.views'

    def setUp(self):
        self.url = reverse('api.activate')
        self.client = Client()
        self.api_user = ApiUser.objects.create(
            email="foo@bar.com",
            password="baz"
        )
        self.auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(b'foo@bar.com:baz').decode("ascii")
        }

    def tearDown(self):
        delete_api_user(email=self.api_user.email)

    def test_sign_up_not_accepted_method(self):
        for method in ['get', 'post', 'put', 'delete']:
            response = getattr(self.client, method)(self.url)
            content = response.json()
            assert response.status_code == 405
            assert content.get('errors') == 'Method not allowed'

    def test_invalid_content_type(self):
        for content_type in ['application/octet-stream', 'text/plain', 'application/xml']:
            response = self.client.patch(
               self.url,
                data={"email": "foo", "password": "bar"},
                content_type=content_type
            )
            content = response.json()
            assert response.status_code == 415
            assert content.get('errors') == 'Invalid content type'

    def test_with_missing_patch_data(self):
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(b'foo@bar.com:baz').decode("ascii")
        }
        response = self.client.patch(
            self.url,
            data={"bar": "foo"},
            content_type='application/json',
            **auth_headers
        )
        content = response.json()
        assert response.status_code == 403
        assert content.get('errors') == 'Token should be sent in the request body.'

    def test_patch_with_no_authorization(self):
        response = self.client.patch(
            self.url,
            data={"token": "foo"},
            content_type='application/json',
        )
        content = response.json()
        assert response.status_code == 403
        assert content.get('errors') == 'HTTP_AUTHORIZATION missing'

    def test_patch_with_incorrect_authorization(self):
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic1 ' + base64.b64encode(b'foo@bar.com:baz').decode("ascii")
        }
        response = self.client.patch(
            self.url,
            data={"token": "foo"},
            content_type='application/json',
            **auth_headers
        )
        content = response.json()
        assert response.status_code == 403
        assert content['errors'] == 'Application only support basic auth.'

    def test_patch_non_match_token(self):
        insert_api_user(email=self.api_user.email, password=self.api_user.password)
        save_token(self.api_user.email, 'abcd')

        response = self.client.patch(
            self.url,
            data={"token": "foo"},
            content_type='application/json',
            **self.auth_headers
        )
        content = response.json()
        assert response.status_code == 403
        assert content['errors'] == 'Provided token not matching the user token.'

    def test_patch_non_match_password(self):
        insert_api_user(email=self.api_user.email, password=self.api_user.password)
        save_token(self.api_user.email, 'abcd')
        auth_headers = {
            'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(b'foo@bar.com:spam').decode("ascii")
        }
        self.api_user.token = "abcd"
        self.api_user.save()
        response = self.client.patch(
            self.url,
            data={"token": f"{self.api_user.token}"},
            content_type='application/json',
            **auth_headers
        )
        content = response.json()

        assert response.status_code == 401
        assert content['errors'] == 'The email or the password provided are wrong.'

    def test_activation_successful(self):
        insert_api_user(email=self.api_user.email, password=self.api_user.password)
        save_token(self.api_user.email, 'abcd')
        now = timezone.now()
        with self.assertLogs(logger=self.logger, level='INFO') as lg:
            lg._replace(output=[])
            response = self.client.patch(
                self.url,
                data={"token": 'abcd'},
                content_type='application/json',
                **self.auth_headers
            )

            self.assertIn(f"User with {self.api_user.email} has been activated", ','.join(lg.output))
        content = response.json()
        assert content['message'] == f"User {self.api_user.email} has been activated."

        user = get_api_user(self.api_user.email)[0]

        assert user[4] == True  # activated
        assert user[3] == 'abcd' # token
        assert  user[5].strftime("%Y-%m-%d %H:%M:%S") == now.strftime("%Y-%m-%d %H:%M:%S")  # token activation date

    def test_token_expired(self):
        now = timezone.now()
        insert_api_user(email=self.api_user.email, password=self.api_user.password)
        save_token(
            email=self.api_user.email,
            token='abcd',
            pref_date=now - relativedelta(minutes=2)
        )
        with self.assertLogs(logger=self.logger, level='INFO') as lg:
            lg._replace(output=[])
            response = self.client.patch(
                self.url,
                data={"token": 'abcd'},
                content_type='application/json',
                **self.auth_headers
            )
            self.assertIn("The token abcd expired. Signup again to receive a new token.", ','.join(lg.output))
        content = response.json()
        assert content['errors'] == "The token abcd expired. Signup again to receive a new token."
