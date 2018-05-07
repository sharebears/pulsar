import json
import flask
from . import bp


@bp.after_app_request
def hook(response):
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
