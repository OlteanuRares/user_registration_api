import base64
from django.contrib.auth.hashers import check_password

def check_user_password(user_password, request):
    """Checks if the api user is authenticated

    :returns: true or false
    """
    if 'HTTP_AUTHORIZATION' not in request.META:
        return False

    auth = request.META['HTTP_AUTHORIZATION'].split()
    if len(auth) != 2:
        return False

    if auth[0].lower() != 'basic':
        return False

    try:
        key, secret = base64.b64decode(auth[1].encode()).decode().split(':')
    except (ValueError, TypeError):
        return False
    return check_password(secret, user_password)
