import flask

bp = flask.Blueprint('users', __name__, url_prefix='/users')

PERMISSIONS = [
    'view_users',  # Ability to view a user page
    'change_password',  # Ability to change user's password
    'edit_settings',  # Edit own user's settings
    'moderate_users',  # User moderation (Staff) (can edit basic permissions)
    'moderate_users_advanced',  # Advanced user moderation (Admin+)
    'no_ip_history',  # IPs of user are not recorded
    'view_cache_keys',  # View accessed and modified cache keys, for debug in production
    'send_invites',  # Send an invite
    'view_invites',  # View information about user's own invites
    'view_invites_others',  # View information about all invites
    'revoke_invites',  # Revoke user's own invites
    'revoke_invites_others',  # Revoke any invite
    'view_api_keys',  # View own API keys
    'view_api_keys_others',  # View any API key
    'revoke_api_keys',  # Revoke own API keys
    'revoke_api_keys_others',  # Revoke any API key
]
