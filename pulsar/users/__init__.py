import flask

bp = flask.Blueprint('users', __name__)

PERMISSIONS = [
    'view_users',
    'view_users_detailed',
    'change_password',
    'change_password_others',
    'no_ip_tracking',
]
