import json
from functools import wraps
from typing import Any, Callable, Dict

import flask
from voluptuous import Invalid, Schema  # noqa

from pulsar import APIException


def validate_data(schema: 'Schema') -> Callable:
    """
    Compare a request's form data to a provided Voluptuous schema.
    If the request data is invalid, an APIException is raised.

    :param schema: A voluptuous Schema object.
    """
    def wrapper(func):
        @wraps(func)
        def new_function(*args, **kwargs):
            try:
                if flask.request.method == 'GET':
                    kwargs.update(schema(flask.request.args.to_dict()))
                else:
                    kwargs.update(schema(get_request_data()))
            except Invalid as e:
                raise APIException(f'Invalid data: {e.msg} (key "{".".join(e.path)}")')
            return func(*args, **kwargs)
        return new_function
    return wrapper


def get_request_data() -> Dict[Any, Any]:
    """
    Turn the incoming json data into a dictionary and remove the CSRF key if present.

    :return:              The unserialized dict sent by the requester.

    :raises APIException: If the sent data cannot be decoded from JSON.
    """
    try:
        raw_data = flask.request.get_data()
        data = json.loads(raw_data) if raw_data else {}
    except ValueError:
        raise APIException(
            'Unable to decode data. Please make sure you are sending valid JSON.')
    if 'csrf_token' in data:
        del data['csrf_token']
    return data
