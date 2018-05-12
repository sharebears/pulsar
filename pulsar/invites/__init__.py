import flask

bp = flask.Blueprint('invites', __name__)

PERMISSIONS = [
    'send_invites',  # Send an invite
    'view_invites',  # View information about user's own invites
    'view_invites_others',  # View information about all invites
    'revoke_invites',  # Revoke user's own invites
    'revoke_invites_others',  # Revoke any invite
]
