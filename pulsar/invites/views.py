import flask
from voluptuous import Schema, Email
from .models import Invite
from .schemas import invite_schema, invites_schema
from pulsar import db, APIException, _404Exception
from pulsar.utils import validate_data, require_permission, choose_user, assert_user
from pulsar.users.schemas import multiple_user_schema

app = flask.current_app
bp = flask.Blueprint('invites', __name__)

user_invite_schema = Schema({
    'email': Email(),
    }, required=True)


@bp.route('/invites/<code>', methods=['GET'])
@require_permission('view_invites')
def view_invite(code):
    invite = Invite.from_code(code)
    if not invite or not assert_user(invite.inviter_id, 'view_invites_others'):
        raise _404Exception(f'Invite {code}')
    return invite_schema.jsonify(invite)


@bp.route('/invites', methods=['GET'])
@bp.route('/invites/user/<int:user_id>', methods=['GET'])
@require_permission('view_invites')
def view_active_invites(user_id=None):
    user = choose_user(user_id, 'view_invites_others')
    return invites_schema.jsonify(user.active_invites)


@bp.route('/invites', methods=['POST'])
@require_permission('send_invites')
@validate_data(user_invite_schema)
def invite_user(email):
    if not app.config['REQUIRE_INVITE_CODE']:
        raise APIException(
            'An invite code is not required to register, so invites have been disabled.')
    if not flask.g.user.invites:
        raise APIException('You do not have an invite to send.')

    invite = Invite.generate_invite(flask.g.user.id, email, flask.request.remote_addr)
    flask.g.user.invites -= 1
    db.session.add(invite)
    db.session.commit()
    return invite_schema.jsonify(invite)


@bp.route('/invites/<code>', methods=['DELETE'])
@require_permission('revoke_invites')
def revoke_invite(code):
    invite = Invite.from_code(code)
    if not invite or not assert_user(invite.inviter_id, 'revoke_invites_others'):
        raise _404Exception(f'Invite {code}')

    invite.active = False
    flask.g.user.invites += 1
    db.session.commit()
    return invite_schema.jsonify(invite)


@bp.route('/invitees', methods=['GET'])
@bp.route('/invitees/user/<int:user_id>', methods=['GET'])
@require_permission('view_invites')
def view_invitees(user_id=None):
    user = choose_user(user_id, 'view_invites_others')
    return multiple_user_schema.jsonify(user.invitees)
