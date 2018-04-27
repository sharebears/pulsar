import flask

bp = flask.Blueprint('invites', __name__)

PERMISSIONS = [
    'send_invites',
    'view_invites',
    'view_invites_others',
    'revoke_invites',
    'revoke_invites_others',
]
