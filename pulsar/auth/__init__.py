import flask

bp = flask.Blueprint('auth', __name__)

PERMISSIONS = [
    'create_api_keys',
    'revoke_api_keys',
    'revoke_api_keys_others',
    'view_api_keys',
    'view_api_keys_others',
    'view_sessions',
    'view_sessions_others',
    'expire_sessions',
    'expire_sessions_others',
]
