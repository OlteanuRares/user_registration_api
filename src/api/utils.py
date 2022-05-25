import random
import string
import psycopg2
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password

from src.api.exceptions import Http500Error, Http400Error


class ApiResponse(object):
    """We use this object to pass from the view the result, a status code
    and extra headers.

    This resembles the HttpResponse, but the content isn't necessarily
    rendered HTML
    """
    def __init__(self, content=None, status=200, headers=None):
        self.content = content
        self.status = status
        self.headers = dict(headers) if headers else {}

    @classmethod
    def from_object(cls, obj):
        """Return an instance of ApiResponse, created from the given object
        """
        if isinstance(obj, cls):
            return obj
        else:
            return ApiResponse(obj)

def get_random_string():
    # get random password pf length 4 with letters, digits, and symbols
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(4))

def get_connection():
    return psycopg2.connect(
        host=settings.DB_DEFAULT_HOST,
        database=settings.DB_DEFAULT_NAME,
        user=settings.DB_DEFAULT_USER,
        password=settings.DB_DEFAULT_PASSWORD
    )

def execute_select_statement(query):
    result, conn = None, None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        result = cur.fetchall()
    except (Exception, psycopg2.DatabaseError) as ex:
        raise Http500Error(message=str(ex))
    finally:
        if conn is not None:
            conn.close()
        return result

def execute_insert_update_statement(query):
    result, conn = None, None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        result = conn.commit()
    except (Exception, psycopg2.DatabaseError) as ex:
        raise Http500Error(message=str(ex))
    finally:
        if conn is not None:
            conn.close()
        return result

def send_activation_email(email, token):
    message = f"Use {token} to activate your account. The code is valid for one minute."
    send_mail(
        subject="Activation code",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )
    return message

def get_api_user(email):
    query = f"select * from api_apiuser where email='{email}' order by created_at desc limit 1;"
    return execute_select_statement(query)

def insert_api_user(email, password):
    now = datetime.utcnow()
    hashed_password = make_password(password)
    query = f"insert into api_apiuser (email, password, token, activated, token_sent_at, created_at) " \
            f"values ('{email}','{hashed_password}', null, false, '{now}', '{now}');"
    return execute_insert_update_statement(query)

def save_token(email, token, pref_date=None):
    now = datetime.utcnow()
    token_activated_at = pref_date or now
    query = f"update api_apiuser set token='{token}', token_sent_at='{token_activated_at}' where email='{email}';"
    return execute_insert_update_statement(query)

def activate_user(api_user_id):
    query = f"update api_apiuser set activated=True where id='{api_user_id}';"
    return execute_insert_update_statement(query)

def token_not_expired(api_user, token):
    utc = pytz.UTC
    now = utc.localize(datetime.utcnow())
    return  now <= api_user[5] + relativedelta(minutes=1)


def get_auth_from_request(request):
    if 'HTTP_AUTHORIZATION' not in request.META:
        raise Http400Error(message="HTTP_AUTHORIZATION missing")

    auth = request.META['HTTP_AUTHORIZATION'].split()
    if len(auth) != 2:
        raise Http400Error(message='Incorrect HTTP_AUTHORIZATION')

    if auth[0].lower() != 'basic':
        raise Http400Error(message='Application only support basic auth.')

    return  base64.b64decode(auth[1].encode()).decode().split(':')


def delete_api_user(email):
    query = f"""delete from api_apiuser where email='{email}'"""
    return execute_insert_update_statement(query)