import flask
from voluptuous import All, Length, Match, Schema

from pulsar import _401Exception, _403Exception, db
from pulsar.auth.models import Session
from pulsar.utils import choose_user, require_permission, validate_data
from pulsar.validators import PASSWORD_REGEX

from . import bp

app = flask.current_app

SETTINGS_SCHEMA = Schema({
    # Length restrictions inaccurate for legacy databases and testing.
    'existing_password': All(str, Length(min=5, max=512)),
    'new_password': Match(PASSWORD_REGEX, msg=(
        'Password must be between 12 and 512 characters and contain at least 1 letter, '
        '1 number, and 1 special character')),
    })


@bp.route('/users/settings', methods=['PUT'])
@bp.route('/users/<int:user_id>/settings', methods=['PUT'])
@require_permission('edit_settings')
@validate_data(SETTINGS_SCHEMA)
def edit_settings(user_id: int =None,
                  existing_password: str =None,
                  new_password: str =None) -> flask.Response:
    """
    Change a user's settings. Requires the ``edit_settings`` permission.
    Requires the ``moderate_users`` permission to change another user's
    settings, which can be done by specifying a ``user_id``.

    .. :quickref: UserSettings; Change settings.

    **Example request**:

    .. sourcecode:: http

       PUT /users/settings HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "existing_password": "y-&~_Wbt7wjkUJdY<j-K",
         "new_password": "an-ev3n-be77er-pa$$w0rd"
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "Settings updated."
       }

    :json string existing_password: User's existing password, not needed
        if setting another user's password with ``moderate_user`` permission.
    :json string new_password: User's new password. Must be 12+ characters and contain
        at least one letter, one number, and one special character.

    :>json string response: Success message

    :statuscode 200: Settings successfully updated
    :statuscode 400: Settings unsuccessfully updated
    :statuscode 403: User does not have permission to change user's settings
    """
    user = choose_user(user_id, 'moderate_users')
    if new_password:
        if not flask.g.user.has_permission('change_password'):
            raise _403Exception(
                message='You do not have permission to change this password.')
        if not existing_password or not user.check_password(existing_password):
            raise _401Exception(message='Invalid existing password.')
        user.set_password(new_password)
        Session.update_many(
            pks=Session.hashes_from_user(user.id),
            update={'expired': True})

    db.session.commit()
    return flask.jsonify('Settings updated.')
