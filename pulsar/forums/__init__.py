import flask

bp = flask.Blueprint('forums', __name__)

PERMISSIONS = [
    'view_forums',
    'create_forum_posts',
    'create_forum_threads',
    'delete_forum_posts',
    'delete_forum_threads',
    'moderate_forums',
    'modify_forums',
    ]
