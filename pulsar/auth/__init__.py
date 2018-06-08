import flask

bp = flask.Blueprint('auth', __name__)

PERMISSIONS = [
    'view_api_keys',  # View own API keys
    'view_api_keys_others',  # View any API key
    'revoke_api_keys',  # Revoke own API keys
    'revoke_api_keys_others',  # Revoke any API key
]
