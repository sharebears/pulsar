import flask
from voluptuous import Schema, Email, All, Range
from voluptuous.validators import Match
from . import bp
from pulsar import db, PASSWORD_REGEX
from pulsar.models import User
from pulsar.utils import validate_data, require_permission

app = flask.current_app

moderate_user_schema = Schema({
    'email': Email(),
    'password': Match(PASSWORD_REGEX, msg=(
        'Password must be 12 or more characters and contain at least 1 letter, '
        '1 number, and 1 special character,')),
    'uploaded': All(int, Range(min=0, max=9223372036854775808)),
    'downloaded': All(int, Range(min=0, max=9223372036854775808)),
    'invites': All(int, Range(min=0, max=2147483648)),
    })


@bp.route('/users/<int:user_id>/moderate', methods=['PUT'])
@require_permission('moderate_users')
@validate_data(moderate_user_schema)
def moderate_user(user_id, email=None, password=None, uploaded=None, downloaded=None,
                  invites=None):
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
    user = User.from_id(user_id, _404='User')

    if email:
        user.email = email
    if password:
        user.set_password(password)
    if uploaded:
        user.uploaded = uploaded
    if downloaded:
        user.downloaded = downloaded
    if invites:
        user.invites = invites

    db.session.commit()
    user.clear_cache()
    return flask.jsonify(user)
