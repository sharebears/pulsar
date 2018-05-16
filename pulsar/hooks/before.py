import json
from collections import defaultdict
from datetime import datetime
from typing import Optional

import flask
import pytz

from pulsar import APIException, _312Exception, _403Exception, cache, db
from pulsar.models import APIKey, Session, User

from . import bp

app = flask.current_app


@bp.before_app_request
def hook() -> None:
    flask.g.user = None
    flask.g.api_key = None
    flask.g.user_session = None
    flask.g.csrf_token = None
    flask.g.cache_keys = defaultdict(set)

    if not check_user_session():
        check_api_key()

    if flask.g.user:
        if not flask.g.user.enabled:
            raise _312Exception

        check_rate_limit()

        # The only unauthorized POST method allowed is registration,
        # which does not have a user global and therefore doesn't require
        # CSRF protection.
        if flask.g.user_session and flask.request.method in ['POST', 'PUT', 'DELETE']:
            check_csrf()


def check_user_session() -> bool:
    """
    Checks to see if the request contains a valid signed session.
    If it exists, set the flask.g.user and flask.g.api_key context globals.

    :return: ``True`` or ``False``, depending on whether or not a session was obtained.
    """
    user_id = flask.session.get('user_id')
    id = flask.session.get('session_id')
    if user_id and id:
        session = Session.from_id(id)  # Implied active_only
        if session and session.user_id == user_id and not session.is_expired():
            flask.g.user = User.from_id(session.user_id)
            flask.g.user_session = session
            flask.g.csrf_token = session.csrf_token
            if flask.g.user.has_permission('no_ip_history'):
                flask.request.environ['REMOTE_ADDR'] = '0.0.0.0'
            update_session_or_key(session)
            return True
    return False


def check_api_key() -> None:
    """
    Checks the request header for an authorization key and, if the key matches
    an active API key, sets the flask.g.user and flask.g.api_key context globals.
    """
    raw_key = parse_key(flask.request.headers)
    if raw_key and len(raw_key) > 10:
        # The API Key stores the identification hash as the first 10 values,
        # and the secret after it, so the key can be looked up and then
        # compared with the hash function.
        api_key = APIKey.from_id(raw_key[:10])  # Implied active_only
        if api_key and api_key.check_key(raw_key[10:]) and not api_key.revoked:
            flask.g.user = User.from_id(api_key.user_id)
            flask.g.api_key = api_key
            if flask.g.user.has_permission('no_ip_history'):
                flask.request.environ['REMOTE_ADDR'] = '0.0.0.0'
            update_session_or_key(api_key)


def update_session_or_key(session_key) -> None:
    """
    Update the provided session or api key's last seen times,
    user agent, and IP fields.

    :param Session/APIKey session_key: The session or API key to update.
    """
    cache_key = f'{session_key.cache_key}_updated'
    if (not cache.get(cache_key)
            or session_key.ip != flask.request.remote_addr
            or session_key.user_agent != flask.request.headers.get('User-Agent')):
        session_key.last_used = datetime.utcnow().replace(tzinfo=pytz.utc)
        session_key.user_agent = flask.request.headers.get('User-Agent')
        session_key.ip = flask.request.remote_addr
        db.session.commit()

        cache.delete(session_key.cache_key)
        cache.set(cache_key, 1, timeout=60 * 2)  # 2 minute wait before next update


def parse_key(headers) -> Optional[str]:
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


def check_rate_limit() -> None:
    """
    Check whether or not a user has exceeded the rate limits specified in the
    config. Rate limits per API key or session and per user are recorded.
    The redis database is used to keep track of caching, by incrementing
    "rate limit" cache keys on each request and setting a timeout on them.
    50 requests / 80 seconds per API key or session and 70 requests / 80 seconds
    per account. Records requests in the cache DB.

    :raises APIException: If the rate limit has been exceeded
    """
    user_cache_key = f'rate_limit_user_{flask.g.user.id}'
    if flask.g.user_session:
        auth_cache_key = f'rate_limit_session_{flask.g.user_session.id}'
    else:  # API key
        auth_cache_key = f'rate_limit_api_key_{flask.g.api_key.id}'

    auth_specific_requests = cache.inc(
        auth_cache_key, timeout=app.config['RATE_LIMIT_AUTH_SPECIFIC'][1])
    if auth_specific_requests > app.config['RATE_LIMIT_AUTH_SPECIFIC'][0]:
        time_left = cache.ttl(auth_cache_key)
        raise APIException('Client rate limit exceeded. '
                           f'{time_left} seconds until lock expires.')

    user_specific_requests = cache.inc(
        user_cache_key, timeout=app.config['RATE_LIMIT_PER_USER'][1])
    if user_specific_requests > app.config['RATE_LIMIT_PER_USER'][0]:
        time_left = cache.ttl(user_cache_key)
        raise APIException('User rate limit exceeded. '
                           f'{time_left} seconds until lock expires.')


def check_csrf() -> None:
    """
    Checks the CSRF token in a HTTP request, and compares it to the authorization key
    of the session/api key used in the request. This function will run and potentially
    raise an exception on every POST/PUT/DELETE request, even if the endpoint does not
    exist. That is intentional, so hidden endpoints are masqueraded from curious users.

    **This function is extremely important, please do not fuck with it.**

    :raises APIException: If input is not JSON serialize.
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
