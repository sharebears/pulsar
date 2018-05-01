import flask
from voluptuous import Schema, Optional
from voluptuous.validators import Match
from .. import bp
from pulsar import db, APIException
from pulsar.auth.models import Session
from pulsar.utils import PASSWORD_REGEX, choose_user, validate_data, require_permission

app = flask.current_app

password_change_schema = Schema({
    Optional('existing_password', default=''): str,
    'new_password': Match(PASSWORD_REGEX, msg=(
        'Password must be 12 or more characters and contain at least 1 letter, '
        '1 number, and 1 special character.')),
    }, required=True)


# TODO: Add Admin Log Decorator
@bp.route('/users/change_password', methods=['PUT'])
@bp.route('/users/<int:user_id>/change_password', methods=['PUT'])
@require_permission('change_password')
@validate_data(password_change_schema)
def change_password(existing_password, new_password, user_id=None):
    """
    Change a user's password. Requires the ``change_password`` permission.
    Requires the ``change_password_others`` permission to change another user's
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
        if setting another user's password with ``change_password_others`` permission.
    :json string new_password: User's new password. Must be 12+ characters and contain
        at least one letter, one number, and one special character.

    :>json string response: success message

    :statuscode 200: password successfully changed
    :statuscode 400: password unsuccessfully changed
    :statuscode 403: user does not have permission to change user's password
    """
    user = choose_user(user_id, 'change_password_others')
    if flask.g.user == user and not user.check_password(existing_password):
        raise APIException('Invalid existing password.')
    user.set_password(new_password)
    Session.expire_all_of_user(user.id)
    db.session.commit()
    return flask.jsonify('Password changed.')
