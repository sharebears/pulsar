import flask

bp = flask.Blueprint('forums', __name__)

# TODO: Flip names so forums is first

PERMISSIONS = [
    'view_forums',  # View the forums
    'create_forum_posts',  # Post in the forums and edit own posts
    'forum_double_post',  # Double post in the forums
    'create_forum_threads',  # Create forum threads
    'modify_forum_subscriptions',  # Add and remove subscriptions to forums and threads
    'modify_forum_posts',  # Edit others' forum posts
    'modify_forum_posts_advanced',  # Manipulate and delete others' forum posts
    'modify_forum_threads',  # Edit forum threads
    'modify_forum_threads_advanced',  # Manipulate and delete others' forum threads
    'modify_forums',  # Manipulate forum categories (add, delete)
    'forums_post_in_locked_threads',  # Post in locked threads
    'modify_forum_polls',  # Manipulate answer choices, feature, sticky polls
    'forums_polls_vote',  # Vote on forum polls
    'no_post_length_limit',  # No post length limit
    ]
