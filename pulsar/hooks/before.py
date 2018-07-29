from collections import defaultdict
from datetime import datetime
from typing import Optional

import flask
import pytz

from pulsar import APIException, _312Exception, _401Exception, cache, db
from pulsar.users.models import APIKey, User

from . import bp

app = flask.current_app


@bp.before_app_request
def hook() -> None:
    flask.g.user = None
    flask.g.api_key = None
    flask.g.cache_keys = defaultdict(set)

    check_api_key()
    if flask.g.user and not flask.g.user.enabled:
        raise _312Exception

    check_rate_limit()


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
        api_key = APIKey.from_pk(raw_key[:10])  # Implied active_only
        if api_key and api_key.check_key(raw_key[10:]) and not api_key.revoked:
            flask.g.user = User.from_pk(api_key.user_id)
            flask.g.api_key = api_key
            if flask.g.user.has_permission('no_ip_history'):
                flask.request.environ['REMOTE_ADDR'] = '0.0.0.0'
            update_api_key(api_key)
        else:
            raise _401Exception


def update_api_key(api_key: APIKey) -> None:
    """
    Update the provided session or api key's last seen times,
    user agent, and IP fields.

    :param session_key: The session or API key to update
    """
    cache_key = f'{api_key.cache_key}_updated'
    if (not cache.get(cache_key)
            or api_key.ip != flask.request.remote_addr
            or api_key.user_agent != flask.request.headers.get('User-Agent')):
        api_key.last_used = datetime.utcnow().replace(tzinfo=pytz.utc)
        api_key.user_agent = flask.request.headers.get('User-Agent')
        api_key.ip = flask.request.remote_addr
        db.session.commit()

        cache.delete(api_key.cache_key)
        cache.set(cache_key, 1, timeout=60 * 2)  # 2 minute wait before next update


def parse_key(headers) -> Optional[str]:
    """
    Parses the header for an API key, and returns it if found.
    The authorization header must be in the following format: ``Token <api key>``.

    :param headers: A dictionary of request headers
    :return:        If present, the key parsed from header
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
    The rate limit can be adjusted in the configuration file.

    :raises APIException: If the rate limit has been exceeded
    """
    if not flask.g.user:
        return check_rate_limit_unauthenticated()

    user_cache_key = f'rate_limit_user_{flask.g.user.id}'
    key_cache_key = f'rate_limit_api_key_{flask.g.api_key.hash}'

    auth_specific_requests = cache.inc(
        key_cache_key, timeout=app.config['RATE_LIMIT_AUTH_SPECIFIC'][1])
    if auth_specific_requests > app.config['RATE_LIMIT_AUTH_SPECIFIC'][0]:
        time_left = cache.ttl(key_cache_key)
        raise APIException(
            f'Client rate limit exceeded. {time_left} seconds until lock expires.')

    user_specific_requests = cache.inc(
        user_cache_key, timeout=app.config['RATE_LIMIT_PER_USER'][1])
    if user_specific_requests > app.config['RATE_LIMIT_PER_USER'][0]:
        time_left = cache.ttl(user_cache_key)
        raise APIException(
            f'User rate limit exceeded. {time_left} seconds until lock expires.')


def check_rate_limit_unauthenticated() -> None:
    """Applies a harsher 30 req / minute to unauthenticated users."""
    cache_key = f'rate_limit_unauth_{flask.request.remote_addr}'
    requests = cache.inc(cache_key, timeout=60)
    if requests > 30:
        time_left = cache.ttl(cache_key)
        raise APIException(
            f'Unauthenticated rate limit exceeded. {time_left} seconds until lock expires.')
