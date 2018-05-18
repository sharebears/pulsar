import flask

bp = flask.Blueprint('forums', __name__)

PERMISSIONS = [
    'view_forums',  # View the forums
    'forum_posts',  # Post in the forums and edit own posts
    'modify_forum_posts',  # Edit others' forum posts
    'create_forum_threads',  # Create forum threads
    'modify_forum_posts_advanced',  # Manipulate and delete others' forum posts
    'modify_forum_threads',  # Edit forum threads
    'modify_forum_threads_advanced',  # Manipulate and delete others' forum threads
    'modify_forums',  # Manipulate forum categories (add, delete)
    ]
