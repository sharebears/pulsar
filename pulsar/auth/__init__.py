import flask

bp = flask.Blueprint('auth', __name__)

PERMISSIONS = [
    'create_api_keys',  # Create API keys for own user
    'view_api_keys',  # View own API keys
    'view_api_keys_others',  # View any API key
    'revoke_api_keys',  # Revoke own API keys
    'revoke_api_keys_others',  # Revoke any API key
    'view_sessions',  # View own sessions
    'view_sessions_others',  # View any session
    'expire_sessions',  # Expire own session
    'expire_sessions_others',  # Expire any session
]
