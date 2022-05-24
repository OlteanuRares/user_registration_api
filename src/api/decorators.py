import json
import logging
import traceback

from functools import wraps
from django.http.response import HttpResponse

from .exceptions import HttpError, Http415Error, Http405Error
from src.api.utils import ApiResponse


logger = logging.getLogger(__name__)


def jsonify(view):
    """Transforms the dictionary returned by the view into a
    json, and sends it as a HttpResponse.

    The view can also return an ApiResponse, which will have extra information,
    regarding the status code and the extra headers to be added to the response
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        headers = {}
        try:
            api_response = ApiResponse.from_object(view(*args, **kwargs))
            raw_response = api_response.content
            status_code = api_response.status
            headers.update(api_response.headers)
        except HttpError as err:
            raw_response = err.response
            status_code = err.status_code
            headers.update(err.headers)
        except Exception as e:
            raw_response = {"errors": ["Internal server error"]}
            status_code = 500
            traceback.print_exc()

        response_body = (json.dumps(raw_response)
                         if raw_response is not None else '')
        response = HttpResponse(status=status_code, content=response_body)
        response['Content-Type'] = 'application/json'
        for header, value in headers.items():
            response[header] = value

        return response

    return wrapper


class restrict_contenttype(object):
    """On requests that have a body, restrict the allowed Content Type

    http://www.w3.org/Protocols/rfc2616/rfc2616-sec7.html#sec7.2.1
    """
    def __init__(self, ctype):
        self.ctype = ctype

    def __call__(self, view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if (self.ctype not in request.META.get('CONTENT_TYPE', []) and
                    request.body):
                raise Http415Error()

            return view(request, *args, **kwargs)
        return wrapper


def require_http_methods(http_methods):
    """Custom method, mimicking django.views.decorators.require_http_methods.

    This throws custom exceptions, instead of returning a HttpResponse
    :param http_methods:
    :return:
    """
    def mediator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method not in http_methods:
                raise Http405Error(allowed_methods=http_methods)
            return func(request, *args, **kwargs)

        return wrapper

    return mediator


def user_api(httpmethods):
    """Decorator - wrapper around @jsonify, @require_http_method,
     and @restrict_contenttype

    The order matters
    """

    def mediator(func):
        @wraps(func)
        @jsonify
        @require_http_methods(httpmethods)
        @restrict_contenttype('application/json')
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return mediator
