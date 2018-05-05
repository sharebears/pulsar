import flask
from voluptuous import Schema, Optional
from voluptuous.validators import Match
from .. import bp
from ..models import User
from pulsar import db, APIException, _404Exception
from pulsar.utils import PASSWORD_REGEX, validate_data, require_permission

app = flask.current_app

moderate_user_schema = Schema({
    Optional('existing_password', default=''): str,
    'password': Match(PASSWORD_REGEX, msg=(
        'Password must be 12 or more characters and contain at least 1 letter, '
        '1 number, and 1 special character.')),
    }, required=True)


@bp.route('/users/<int:user_id>/moderate', methods=['PUT'])
@require_permission('moderate_user')
@validate_data(moderate_user_schema)
def moderate_user(user_id, password):
    """
    Moderate a user - change password for them, alter stats, modify basic permissions,
    etc.

    .. :quickref: User; Moderate user.

    **Example request**:

    .. sourcecode:: http

       PUT /users/1/moderate HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "password": "an-ev3n-be77er-pa$$w0rd"
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "id": 1,
           "username": "lights",
           "email": "lights@pul.sar"
         }
       }

    :json string password: User's new password. Must be 12+ characters and contain
        at least one letter, one number, and one special character.

    :>json string response: Success message

    :statuscode 200: User successfully moderated
    :statuscode 400: User unsuccessfully moderated
    :statuscode 403: User does not have permission to moderate some parts of user
    """
    user = User.from_id(user_id)
    if not user:
        raise _404Exception(f'User {user_id}')
    return flask.jsonify('User moderated.')
