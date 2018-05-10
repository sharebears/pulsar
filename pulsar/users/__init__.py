import flask

bp = flask.Blueprint('users', __name__)

PERMISSIONS = [
    'view_users',
    'change_password',
    'moderate_users',
    'no_ip_tracking',
]
