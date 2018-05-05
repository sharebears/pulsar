import flask

bp = flask.Blueprint('users', __name__)

PERMISSIONS = [
    'view_users',
    'change_password',
    'change_password_others',
    'no_ip_tracking',
]
