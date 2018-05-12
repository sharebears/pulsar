import flask

bp = flask.Blueprint('users', __name__)

PERMISSIONS = [
    'view_users',
    'change_password',
    'moderate_users',
    'no_ip_tracking',
    'view_cache_keys',  # View accessed and modified cache keys, for debug in production
]
