import json
import logging
from django.contrib.auth.hashers import check_password

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
    token_not_expired,
    get_auth_from_request
)
from src.api.exceptions import Http500Error, Http400Error, Http404Error, Http401Error



logger = logging.getLogger(__name__)


class SignupView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(user_api(['POST']))
    def dispatch(self, request, *args, **kwargs):
        return super(SignupView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        content = json.loads(request.body)
        email = content.get('email')
        password = content.get('password')
        if not all([email, password]):
            raise Http400Error(message='Email, and password should be sent in the request body.')
        try:
            api_user = get_api_user(email)
        except Exception as ex:
            logger.error(str(ex))
            raise Http500Error(message=f"Failed to fetch data because {ex.message}")

        logger.info("Check if the email already in database.")
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
            content={
                "message" : f'Activation mail sent to {email}.',
                'token': token
            }
        )


class ActivateView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(user_api(['PATCH']))
    def dispatch(self, request, *args, **kwargs):
        return super(ActivateView, self).dispatch(request, *args, **kwargs)

    def patch(self, request):
        content = json.loads(request.body)
        token = content.get('token')

        logger.info('Getting email and password from request')
        try:
            email, password = get_auth_from_request(request)
        except Http400Error as ex:
            raise Http400Error(message=ex.response['errors'])
        except Exception as ex:
            raise Http400Error(message=str(ex))

        if not token:
            logger.info('Token should be sent in the request body.')
            raise Http400Error(message='Token should be sent in the request body.')

        logger.info('Get api user')
        try:
            api_user = get_api_user(email)
        except Http500Error as ex:
            logger.error(str(ex))
            raise Http500Error(message=f"Failed to fetch data because {ex.message}")
        if not len(api_user):
            raise Http404Error(message=f"User {email} not found.")
        api_user = api_user[0]
        logger.info('Check password')
        if not check_password(password, api_user[2]):
            raise Http401Error(message=f"The email or the password provided are wrong.")
        logger.info("User and password are matching.")

        if api_user[4]:
            return ApiResponse(content=f"User {email} already active.")

        same_token = api_user[3] == token
        if not same_token:
            raise Http400Error(f"Provided token not matching the user token.")
        logger.info('Check token validity.')
        if token_not_expired(api_user=api_user, token=token):
            try:
                activate_user(api_user_id=api_user[0])
                logger.info(f"User with {email} has been activated")
            except Exception as ex:
                raise Http500Error(message=f"Activation failed becvause {str(ex)}")
        else:
            logger.info(f'The token {token} expired. Signup again to receive a new token.')
            raise Http400Error(message=f'The token {token} expired. Signup again to receive a new token.')

        return ApiResponse(content={
            'message': f"User {email} has been activated.",
        })
