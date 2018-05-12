import flask

bp = flask.Blueprint('permissions', __name__)

PERMISSIONS = [
    'modify_permissions',  # View all permissions and modify permissions of users
    'modify_user_classes',  # Modify permissions of and create user classes
]
