import flask

bp = flask.Blueprint('permissions', __name__)

PERMISSIONS = [
    'manipulate_permissions',
    'list_permissions',
    'list_permissions_others',
    'list_user_classes',
    'modify_user_classes',
]
