import json

import flask

from . import bp


@bp.after_app_request
def hook(response):
    wrap_response(response)
    return response


def wrap_response(response: 'flask.Response') -> 'flask.Response':
    """
    Wrap response with the homogenized response dictionary, containing
    a ``status`` key and, if the request came with session-based
    authentication, a ``csrf_token`` key.

    :param Response response: The flask response en route to user
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

    if flask.g.user and flask.g.user.has_permission('view_cache_keys'):
        # Can't serialize sets to JSON
        for key, value in flask.g.cache_keys.items():
            flask.g.cache_keys[key] = list(value)
        response_data['cache_keys'] = flask.g.cache_keys

    response.set_data(json.dumps(response_data))
