import flask
from voluptuous import Any, Optional, Schema
from voluptuous.validators import Email, Match

from pulsar.users.models import User
from pulsar.utils import require_permission, validate_data
from pulsar.validators import PASSWORD_REGEX, ValInviteCode, ValUsername

from . import bp

app = flask.current_app


@bp.route('/<int:user_id>', methods=['GET'])
@require_permission('view_users')
def get_user(user_id: int) -> flask.Response:
    """
    Return general information about a user with the given user ID.  If the
    user is getting information about themselves, the API will return more
    detailed data about the user. If the requester has the
    ``moderate_users`` permission, the API will return *even more* data.

    .. :quickref: User; Get user information.

    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "<User>"
       }

    :statuscode 200: User exists
    :statuscode 404: User does not exist
    """
    return flask.jsonify(User.from_pk(user_id, _404=True))


CREATE_USER_SCHEMA = Schema({
    'username': ValUsername,
    'password': Match(PASSWORD_REGEX, msg=(
        'Password must be between 12 and 512 characters and contain at least 1 letter, '
        '1 number, and 1 special character')),
    'email': Email(),
    Optional('code', default=None): Any(str, None),
}, required=True)


@bp.route('', methods=['POST'])
@validate_data(CREATE_USER_SCHEMA)
def register(username: str,
             password: str,
             email: str,
             code: str = None) -> flask.Response:
    """
    Creates a user account with the provided credentials.
    An invite code may be required for registration.

    .. :quickref: User; Register a new user.

    **Example request**:

    .. parsed-literal::

       POST /register HTTP/1.1

       {
         "username": "user_one",
         "password": "y-&~_Wbt7wjkUJdY<j-K",
         "email": "user_one@pul.sar",
         "code": "my-invite-code"
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": {
           "username": "lights"
         }
       }

    :json username: Desired username: must start with an alphanumeric
        character and can only contain alphanumeric characters,
        underscores, hyphens, and periods.
    :json password: Desired password: must be 12+ characters and contain
        at least one letter, one number, and one special character.
    :json email: A valid email address to receive the confirmation email,
        as well as account or security related emails in the future.
    :json code: (Optional) An invite code from another member. Required
        for registration if the site is invite only, otherwise ignored.

    :>jsonarr string username: username the user signed up with

    :statuscode 200: registration successful
    :statuscode 400: registration unsuccessful
    """
    ValInviteCode(code)
    user = User.new(
        username=username,
        password=password,
        email=email)
    return flask.jsonify({'username': user.username})
