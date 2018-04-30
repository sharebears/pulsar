import flask
from functools import wraps
from voluptuous import Invalid
from pulsar import APIException


def validate_data(schema):
    """
    Compare a request's form data to a provided Voluptuous schema.
    If the request data is invalid, an APIException is raised.
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


def get_request_data():
    "Turn the incoming json data into a dictionary and remove the CSRF key if present."
    data = flask.request.get_json() or {}
    if 'csrf_token' in data:
        del data['csrf_token']
    return data


def bool_get(val):
    """
    Takes a string value and returns a boolean based on the input, since GET requests
    always come as strings. '1' and 'true' return True, while '0' and 'false'
    return False. Any other input raises an Invalid exception.
    """
    if isinstance(val, bool):
        return val
    elif isinstance(val, str):
        if val == '1' or val.lower() == 'true':
            return True
        elif val == '0' or val.lower() == 'false':
            return False
    raise Invalid('boolean must be "1", "true", "0", or "false" (case insensitive)')
