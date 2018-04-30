import flask
from voluptuous import Schema, Email, Optional
from . import bp
from .models import Invite
from .schemas import invite_schema, invites_schema
from pulsar import db, APIException, _404Exception
from pulsar.utils import (validate_data, require_permission,
                          choose_user, assert_user, bool_get)

app = flask.current_app


@bp.route('/invites/<code>', methods=['GET'])
@require_permission('view_invites')
def view_invite(code):
    """
    View the details of an invite. Requires the `view_invites` permission.
    Requires the `view_invites_others` permission to view another user's invites.

    .. :quickref: Invite; View an active invite.

    **Example request**:

    .. sourcecode:: http

       GET /invites/an-invite-code HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "active": true,
           "code": "an-invite-code",
           "time-sent": "1970-01-01T00:00:00.000001+00:00",
           "email": "bright@pul.sar",
           "invitee": null
         }
       }

    :>jsonarr boolean active: whether or not the invite is active/usable
    :>jsonarr string code: the invite code
    :>jsonarr string time-sent: time the invite was sent
    :>jsonarr string email: the email that the invite was sent to
    :>jsonarr dict invitee: the user invited by the invite

    :statuscode 200: view successful
    :statuscode 404: invite does not exist or user cannot view invite
    """
    invite = Invite.from_code(code, include_dead=True)
    if not invite or not assert_user(invite.inviter_id, 'view_invites_others'):
        raise _404Exception(f'Invite {code}')
    return invite_schema.jsonify(invite)


view_invites_schema = Schema({
    Optional('used', default=False): bool_get,
    Optional('include_dead', default=False): bool_get,
    }, required=True)


@bp.route('/invites', methods=['GET'])
@bp.route('/invites/user/<int:user_id>', methods=['GET'])
@require_permission('view_invites')
@validate_data(view_invites_schema)
def view_invites(used, include_dead, user_id=None):
    """
    View sent invites. If a user_id is specified, only invites sent by that user
    will be returned, otherwise only your invites are returned. If requester has
    the `view_invites_others` permission, they can view sent invites of another user.

    .. :quickref: Invite; View multiple invites.

    **Example request**:

    .. sourcecode:: http

       GET /invites HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           {
             "active": true,
             "code": "an-invite-code",
             "time-sent": "1970-01-01T00:00:00.000001+00:00",
             "email": "bright@pul.sar",
             "invitee": null
           },
           {
             "active": false,
             "code": "another-invite-code",
             "time-sent": "1970-01-01T00:00:00.000002+00:00",
             "email": "bitsu@qua.sar",
             "invitee": {
               "id": 2,
               "username": "bitsu",
               "other-keys": "other-values"
             }
           }
         ]
       }

    :query boolean used: (optional) whether or not to only show used invites
        (overrides include_dead)
    :query boolean include_dead: (optional) whether or not to include inactive invites

    :>json list response: a list of invite data

    :>jsonarr boolean active: whether or not the invite is active/usable
    :>jsonarr string code: the invite code
    :>jsonarr string time-sent: time the invite was sent
    :>jsonarr string email: the email that the invite was sent to
    :>jsonarr dict invitee: the user invited by the invite

    :statuscode 200: view successful
    :statuscode 403: user does not have permission to view invites
    """
    user = choose_user(user_id, 'view_invites_others')
    invites = Invite.from_inviter(user.id, include_dead=(include_dead or used))
    if used:
        invites = [invite for invite in invites if invite.invitee_id]
    return invites_schema.jsonify(invites)


user_invite_schema = Schema({
    'email': Email(),
    }, required=True)


@bp.route('/invites', methods=['POST'])
@require_permission('send_invites')
@validate_data(user_invite_schema)
def invite_user(email):
    """
    Sends an invite to the provided email address. Requires the `send_invites`
    permission. If the site is open registration, this endpoint will raise a
    400 Exception.

    .. :quickref: Invite; Send an invite.

    **Example request**:

    .. sourcecode:: http

       POST /invites/an-invite-code HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "email": "bright@puls.ar"
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "active": true,
           "code": "an-invite-code",
           "time-sent": "1970-01-01T00:00:00.000001+00:00",
           "email": "bright@pul.sar",
           "invitee": null
         }
       }

    :<json string email: email to send the invite to

    :>jsonarr boolean active: whether or not the invite is active/usable (always true)
    :>jsonarr string code: the invite code
    :>jsonarr string time-sent: time the invite was sent
    :>jsonarr string email: the email that the invite was sent to
    :>jsonarr dict invitee: the user invited by the invite

    :statuscode 200: successfully sent invite
    :statuscode 400: unable to send invites or incorrect email
    :statuscode 403: unauthorized to send invites
    """
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
    """
    Revokes an active invite code, preventing it from being used. The
    invite is returned to the user's account. Requires the
    `revoke_invites` permission to revoke one's own sent invite, and the
    `revoke_invites_others` permission to revoke another user's invites.

    .. :quickref: Invite; Revoke an active invite.

    **Example request**:

    .. sourcecode:: http

       DELETE /invites/an-invite-code HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "active": false,
           "code": "an-invite-code",
           "time-sent": "1970-01-01T00:00:00.000001+00:00",
           "email": "bright@pul.sar",
           "invitee": null
         }
       }

    :>jsonarr boolean active: whether or not the invite is active/usable
    :>jsonarr string code: the invite code
    :>jsonarr string time-sent: time the invite was sent
    :>jsonarr string email: the email that the invite was sent to
    :>jsonarr dict invitee: the user invited by the invite

    :statuscode 200: revocation successful
    :statuscode 403: unauthorized to revoke invites
    :statuscode 404: invite does not exist or user cannot view invite
    """
    invite = Invite.from_code(code)
    if not invite or not assert_user(invite.inviter_id, 'revoke_invites_others'):
        raise _404Exception(f'Invite {code}')

    invite.active = False
    flask.g.user.invites += 1
    db.session.commit()
    return invite_schema.jsonify(invite)
