import traceback


class HttpError(Exception):
    """Base class for the API 4xx and 5xx status codes for the responses.
    ..because Django doesn't have  good exceptions other than Http404

    Use these classes for a better separation between error message and
        message format
    """

    def __init__(self, message=None, status_code=None, headers=None, extra_headers=None, *args, **kwargs):
        """
         :param message:        The error message
         :param status_code:    The status code of the response
         :param headers:        The headers to be used when these headers overwrite HttpError.headers
         :param extra_headers:  Extra headers (added to HttpError.headers)
        """

        if status_code:
            self.status_code = status_code

        if message is None:
            message = getattr(self, 'default_message')

        if headers is None:
            if self.headers is None:
                headers = {}
            else:
                headers = dict(self.headers)

        if extra_headers is not None:
            headers.update(extra_headers)

        self.response = {'errors': message}
        self.headers = headers
        super(HttpError, self).__init__(*args, **kwargs)
        traceback.print_exc()

class Http400Error(HttpError):
    """Bad Request
    """
    status_code = 403
    default_message = 'Bad Request'
    headers = {}


class Http401Error(HttpError):
    """Unauthorized
    """
    status_code = 401
    default_message = 'Unauthorized'
    headers = {'WWW-Authenticate': 'Basic realm="src.api"'}


class Http404Error(HttpError):
    """Not found
    """
    status_code = 404
    default_message = 'No resource found'
    headers = {}

class Http405Error(HttpError):
    """Method not allowed - with customizable message and automatic handling
    of the `Allow` header
    """
    status_code = 405
    default_message = 'Method not allowed'

    def __init__(self, response=None, status_code=None, headers=None,
                 extra_headers=None, allowed_methods=None, *args, **kwargs):

        headers = headers or {}
        extra_headers = extra_headers or {}

        if allowed_methods:
            extra_headers.update({'Allow': ', '.join(allowed_methods)})

        super(Http405Error, self).__init__(response, status_code, headers,
                                           extra_headers, *args, **kwargs)


class Http415Error(HttpError):
    """Unsupported media type
    """
    status_code = 415
    default_message = 'Invalid content type'


class Http500Error(HttpError):
    """Internal server error"""
    status_code = 500
    default_message = ('An internal server error occurred. We apologize '
                       'for the inconvenience.')
    headers = {}

