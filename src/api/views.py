import json
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from src.api.decorators import user_api
from src.api.utils import (
    ApiResponse,
    get_api_user,
    insert_api_user,
    send_activation_email,
    get_random_string,
    save_token,
    activate_user,
    token_not_expired
)
from src.api.exceptions import Http500Error, Http400Error, Http404Error, Http401Error
from src.api.auth import check_user_password


logger = logging.getLogger(__name__)


class SignupView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(user_api(['POST']))
    def dispatch(self, request, *args, **kwargs):
        return super(SignupView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        api_user = None
        content = json.loads(request.body)
        email = content.get('email')
        password = content.get('password')
        if not all([email, password]):
            raise Http400Error(message='Email, and password should be sent in the request body.')

        logger.info("Check if the email already in database..")
        try:
            api_user = get_api_user(email)
        except Http500Error as ex:
            logger.error(str(ex))
            raise Http500Error(message=f"Failed to fetch data because {ex.message}")

        if api_user:
            logger.info(f'User with {email} already exists.')
        else :
            # save user if not exists
            logger.info('Save api user to database.')
            try:
                insert_api_user(email, password)
                logger.info(f"User with {email} has been saved().")
            except Exception as ex:
                logger.error(str(ex))
                raise Http500Error(message=f"Failed to save the user because {ex.message}")

        logger.info("Generate activation token and send email with activation link.")
        try:
            token = get_random_string()
            activation_url = send_activation_email(email, token)
            save_token(
                token=token,
                email=email
            )
            logger.info(f'Activation mail sent to {email}.')
        except Exception as ex:
            logger.error(str(ex))
            raise Http500Error(message=f'Failed to send email at {email} because {str(ex)}.')

        return ApiResponse(
            status=201,
            content=f'Activation mail sent to {email} with the token: {activation_url}.'
        )


class ActivateView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(user_api(['PATCH']))
    def dispatch(self, request, *args, **kwargs):
        return super(ActivateView, self).dispatch(request, *args, **kwargs)

    def patch(self, request):
        api_user = None
        content = json.loads(request.body)
        email = content.get('email')
        password = content.get('password')
        token = content.get('token')

        if not all([email, password, token]):
            raise Http400Error(message='Email, password and token should be sent in the request body.')

        try:
            api_user = get_api_user(email)[0]
        except Http500Error as ex:
            logger.error(str(ex))
            raise Http500Error(message=f"Failed to fetch data because {ex.message}")

        if not api_user:
            raise Http404Error(message=f"User with {email} not found.")

        if not check_user_password(user_password=api_user[2], request=request):
            raise Http401Error(message=f"The email or the password provided are wrong.")

        logger.info("User and password are matching.")

        if api_user[4]:
            return ApiResponse(content=f"User {email} already active.")

        same_token = api_user[3] == token
        if not same_token:
            raise Http400Error(f"Provided token not matching the user token.")

        if token_not_expired(api_user=api_user, token=token):
            try:
                activate_user(api_user_id=api_user[0])
            except Exception as ex:
                raise Http500Error(message=f"Activation failed becvause {str(ex)}")
        else:
            logger.info(f'The token {token} expired. Signup again to receive a new token.')
            raise Http400Error(message=f'The token {token} expired. Signup again to receive a new token.')

        return ApiResponse(content=f"User {email} has been activated.")
