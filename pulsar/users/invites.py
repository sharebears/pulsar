import flask
from voluptuous import Email, Optional, Schema

from pulsar import APIException, db
from pulsar.users.models import Invite
from pulsar.utils import choose_user, require_permission, validate_data
from pulsar.validators import BoolGET

from . import bp

app = flask.current_app


VIEW_INVITE_SCHEMA = Schema({
    'code': str,
    }, required=True)


@bp.route('/invite', methods=['GET'])
@require_permission('view_invites')
@validate_data(VIEW_INVITE_SCHEMA)
def view_invite(code: str) -> flask.Response:
    """
    View the details of an invite. Requires the ``view_invites`` permission.
    Requires the ``view_invites_others`` permission to view another user's invites.

    .. :quickref: Invite; View an active invite.

    **Example request**:

    .. parsed-literal::

       GET /invite HTTP/1.1

       {
         "code": "an-invite-code"
       }

    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "<Invite>"
       }

    :statuscode 200: View successful
    :statuscode 404: Invite does not exist or user cannot view invite
    """
    return flask.jsonify(Invite.from_pk(
        code, include_dead=True, _404=True, asrt='view_invites_others'))


VIEW_INVITES_SCHEMA = Schema({
    Optional('used', default=False): BoolGET,
    Optional('include_dead', default=False): BoolGET,
    }, required=True)


@bp.route('/invites', methods=['GET'])
@bp.route('/invites/user/<int:user_id>', methods=['GET'])
@require_permission('view_invites')
@validate_data(VIEW_INVITES_SCHEMA)
def view_invites(used: bool,
                 include_dead: bool,
                 user_id: int = None) -> flask.Response:
    """
    View sent invites. If a user_id is specified, only invites sent by that user
    will be returned, otherwise only your invites are returned. If requester has
    the ``view_invites_others`` permission, they can view sent invites of another user.

    .. :quickref: Invite; View multiple invites.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": [
            "<Invite>",
            "<Invite>"
         ]
       }

    :query boolean used: (Optional) Whether or not to only show used invites
        (overrides ``include_dead``)
    :query boolean include_dead: (Optional) Whether or not to include expired invites

    :>json list response: A list of invites

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view user's invites
    """
    user = choose_user(user_id, 'view_invites_others')
    invites = Invite.from_inviter(user.id, include_dead=include_dead, used=used)
    return flask.jsonify(invites)


USER_INVITE_SCHEMA = Schema({
    'email': Email(),
    }, required=True)


@bp.route('/invites', methods=['POST'])
@require_permission('send_invites')
@validate_data(USER_INVITE_SCHEMA)
def invite_user(email: str):
    """
    Sends an invite to the provided email address. Requires the ``send_invites``
    permission. If the site is open registration, this endpoint will raise a
    400 Exception.

    .. :quickref: Invite; Send an invite.

    **Example request**:

    .. parsed-literal::

       POST /invites/an-invite-code HTTP/1.1

       {
         "email": "bright@puls.ar"
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<Invite>"
       }

    :<json string email: E-mail to send the invite to

    :statuscode 200: Successfully sent invite
    :statuscode 400: Unable to send invites or incorrect email
    :statuscode 403: Unauthorized to send invites
    """
    if not app.config['REQUIRE_INVITE_CODE']:
        raise APIException(
            'An invite code is not required to register, so invites have been disabled.')
    if not flask.g.user.invites:
        raise APIException('You do not have an invite to send.')

    invite = Invite.new(
        inviter_id=flask.g.user.id,
        email=email,
        ip=flask.request.remote_addr)
    flask.g.user.invites -= 1
    db.session.commit()
    return flask.jsonify(invite)


@bp.route('/invite', methods=['DELETE'])
@require_permission('revoke_invites')
@validate_data(VIEW_INVITE_SCHEMA)
def revoke_invite(code: str) -> flask.Response:
    """
    Revokes an active invite code, preventing it from being used. The
    invite is returned to the user's account. Requires the
    ``revoke_invites`` permission to revoke one's own sent invite, and the
    ``revoke_invites_others`` permission to revoke another user's invites.

    .. :quickref: Invite; Revoke an active invite.

    **Example request**:

    .. parsed-literal::

       DELETE /invite HTTP/1.1

       {
         "id": "an-invite-code"
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<Invite>"
       }

    :statuscode 200: Revocation successful
    :statuscode 403: Unauthorized to revoke invites
    :statuscode 404: Invite does not exist or user cannot view invite
    """
    invite = Invite.from_pk(code, _404=True, asrt='revoke_invites_others')
    invite.expired = True
    invite.inviter.invites += 1
    db.session.commit()
    return flask.jsonify(invite)
