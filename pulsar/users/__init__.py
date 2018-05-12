import flask

bp = flask.Blueprint('users', __name__)

PERMISSIONS = [
    'view_users',  # Ability to view a user page
    'change_password',  # Ability to change user's password
    'edit_settings',  # Edit own user's settings
    'moderate_users',  # User moderation (Staff)
    'moderate_users_advanced',  # Advanced user moderation (Admin+)
    'no_ip_tracking',  # IPs of user are not recorded
    'view_cache_keys',  # View accessed and modified cache keys, for debug in production
]
