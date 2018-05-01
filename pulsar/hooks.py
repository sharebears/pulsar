import json
import pytz
import flask
from datetime import datetime
from pulsar import db, _403Exception, APIException
from pulsar.auth.models import Session, APIKey

bp = flask.Blueprint('hooks', __name__)


@bp.before_app_request
def before_hook():
    """
    Before relaying the request to the proper controller, check authentication,
    wipe requester IP if the 'no_ip_history' permission is set, and if a user is found,
    validate any POST requests to ensure that no CSRF is occuring.
    """
    flask.g.user = None
    flask.g.api_key = None
    flask.g.user_session = None
    flask.g.csrf_token = None

    if not check_user_session():
        check_api_key()

    if flask.g.user:
        if flask.g.user.has_permission('no_ip_history'):
            flask.request.environ['REMOTE_ADDR'] = '0.0.0.0'

        # The only unauthorized POST method allowed is registration,
        # which does not have a user global and therefore doesn't require
        # CSRF protection.
        if flask.g.user_session and flask.request.method in ['POST', 'PUT', 'DELETE']:
            check_csrf()


@bp.after_app_request
def after_hook(response):
    """
    After receiving a response from the controller, wrap it in a standardized
    response dictionary and re-serialize it as JSON. Set the `status` key per
    the status_code, and if the request came from a session, add the csrf_token
    to the response.

    :param Response response: A response object with a JSON serialized message.
    """
    try:
        data = json.loads(response.get_data())
    except ValueError:  # pragma: no cover
        data = 'Could not encode response.'

    response_data = {
        'status': 'success' if response.status_code // 100 == 2 else 'failed',
        'response': data,
        }

    if getattr(flask.g, 'csrf_token', None):
        response_data['csrf_token'] = flask.g.csrf_token

    response.set_data(json.dumps(response_data))

    return response


def check_user_session():
    """
    Checks to see if the request contains a valid signed session.
    If it exists, set the flask.g.user and flask.g.api_key context globals.

    :return: ``True`` or ``False``, depending on whether or not a session was obtained.
    """
    user_id = flask.session.get('user_id')
    hash = flask.session.get('session_hash')
    if user_id and hash:
        session = Session.from_hash(hash)  # Implied active_only
        if session and session.user_id == user_id:
            flask.g.user = session.user
            flask.g.user_session = session
            flask.g.csrf_token = session.csrf_token
            update_session_or_key(session)
            return True
    return False


def check_api_key():
    """
    Checks the request header for an authorization key and, if the key matches
    an active API key, sets the flask.g.user and flask.g.api_key context globals.
    """
    raw_key = parse_key(flask.request.headers)
    if raw_key and len(raw_key) > 10:
        # The API Key stores the identification hash as the first 10 values,
        # and the secret after it, so the key can be looked up and then
        # compared with the hash function.
        api_key = APIKey.from_hash(raw_key[:10])  # Implied active_only
        if api_key and api_key.check_key(raw_key[10:]):
            flask.g.user = api_key.user
            flask.g.api_key = api_key
            update_session_or_key(api_key)


def update_session_or_key(session_key):
    """
    Update the provided session or api key's last seen times,
    user agent, and IP fields.

    :param Session/APIKey session_key: The session or API key to update.
    """
    session_key.last_used = datetime.utcnow().replace(tzinfo=pytz.utc)
    session_key.user_agent = flask.request.headers.get('User-Agent')

    if not flask.g.user.has_permission('no_ip_history'):
        session_key.ip = flask.request.remote_addr

    db.session.commit()


def parse_key(headers):
    """
    Parses the header for an API key, and returns it if found.
    The authorization header must be in the following format: ``Token <api key>``.

    :param dict headers: A dictionary of request headers.
    :return: If present, the API Key ``str`` parsed from header, otherwise ``None``.
    """
    auth = headers.get('Authorization')
    if auth:
        parts = auth.split()
        if len(parts) == 2 and parts[0] == 'Token':
            return parts[1]
    return None


def check_csrf():
    """
    Checks the CSRF token in a HTTP request, and compares it to the authorization key
    of the session/api key used in the request. This function will run and potentially
    raise an exception on every POST/PUT/DELETE request, even if the endpoint does not
    exist. That is intentional, so hidden endpoints are masqueraded from curious users.

    **This function is extremely important, please do not fuck with it.**

    :raises APIException: If input is not JSON serializable.
    :raises _403Exception: If user has incorrect csrf_token.
    """
    data = flask.request.get_data()
    try:
        token = json.loads(data).get('csrf_token') if data else None
    except ValueError:
        raise APIException('Malformed input. Is it JSON?')

    # In the rare chance they have no csrf_token, always error.
    if not flask.g.csrf_token or flask.g.csrf_token != token:
        raise _403Exception(message='Invalid authorization key.')
