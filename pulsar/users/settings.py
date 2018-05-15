import flask
from voluptuous import Schema, Match, All, Length
from . import bp
from pulsar import db, PASSWORD_REGEX, _401Exception, _403Exception
from pulsar.models import Session
from pulsar.utils import choose_user, validate_data, require_permission

app = flask.current_app

settings_schema = Schema({
    # Length restrictions inaccurate for legacy databases and testing.
    'existing_password': All(str, Length(min=4, max=512)),
    'new_password': Match(PASSWORD_REGEX, msg=(
        'Password must between 12 and 512 characters and contain at least 1 letter, '
        '1 number, and 1 special character.')),
    })


@bp.route('/users/settings', methods=['PUT'])
@bp.route('/users/<int:user_id>/settings', methods=['PUT'])
@require_permission('edit_settings')
@validate_data(settings_schema)
def edit_settings(user_id=None, existing_password=None, new_password=None):
    # TODO: Fix documentation
    """
    Change a user's password. Requires the ``change_password`` permission.
    Requires the ``moderate_users`` permission to change another user's
    password, which can be done by specifying a ``user_id``.

    .. :quickref: Password; Change password.

    **Example request**:

    .. sourcecode:: http

       PUT /change_password HTTP/1.1
       Host: pul.sar
       Accept: application/json

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
         "response": "Password changed."
       }

    :json string existing_password: User's existing password, not needed
        if setting another user's password with ``moderate_user`` permission.
    :json string new_password: User's new password. Must be 12+ characters and contain
        at least one letter, one number, and one special character.

    :>json string response: Success message

    :statuscode 200: Password successfully changed
    :statuscode 400: Password unsuccessfully changed
    :statuscode 403: User does not have permission to change user's password
    """
    user = choose_user(user_id, 'moderate_users')

    if new_password:
        if not flask.g.user.has_permission('change_password'):
            raise _403Exception(
                message='You do not have permission to change this password.')
        if not user.check_password(existing_password):
            raise _401Exception(message='Invalid existing password.')
        user.set_password(new_password)
        Session.expire_all_of_user(user.id)

    db.session.commit()
    user.clear_cache()
    return flask.jsonify('Settings updated.')
