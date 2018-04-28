import pytz
import flask
from datetime import datetime
from sqlalchemy.sql import func
from voluptuous import Schema, Optional, Any
from voluptuous.validators import Email, Match

from .. import bp
from pulsar.invites.models import Invite
from pulsar import db, APIException
from pulsar.utils import USERNAME_REGEX, PASSWORD_REGEX, validate_data
from pulsar.users.models import User
from pulsar.users.schemas import user_schema

app = flask.current_app

registration_schema = Schema({
    'username': Match(USERNAME_REGEX, msg=(
        'Usernames must start with an alphanumeric character and can only contain '
        'alphanumeric characters, underscores, hyphens, and periods.')),
    'password': Match(PASSWORD_REGEX, msg=(
        'Password must be 12 or more characters and contain at least 1 letter, '
        '1 number, and 1 special character.')),
    'email': Email(),
    Optional('code', default=None): Any(str, None),
}, required=True)


@bp.route('/register', methods=['POST'])
@validate_data(registration_schema)
def register(username, password, email, code):
    """
    Creates a user account with the provided credentials.
    An invite code may be required for registration.

    .. :quickref: User; Register a new user.

    **Example request**:

    .. sourcecode:: http

       POST /register HTTP/1.1
       Host: puls.ar
       Accept: application/json
       Content-Type: application/json

       {
         "username": "lights",
         "password": "y-&~_Wbt7wjkUJdY<j-K",
         "email": "lights@pul.sar",
         "code": "my-invite-code"
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
           "invites": 0
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

    :statuscode 200: registration successful
    :statuscode 400: registration unsuccessful
    """
    if app.config['REQUIRE_INVITE_CODE']:
        validate_invite_code(code)
    validate_username(username)

    user = User(
        username=username,
        password=password,
        email=email)
    db.session.add(user)
    db.session.commit()
    return user_schema.jsonify(user)


def validate_username(username):
    """
    Ensures that a username is not taken and that it matches the required length
    and doesn't contain any invalid characters.
    """
    if (User.query.filter(func.lower(User.username) == username.lower()).one_or_none()):
        raise APIException(f'Another user already has the username `{username}`.')


def validate_invite_code(code):
    """
    Check an invite code against existing invite codes;
    Raises an APIException if the code isn't valid.
    """
    invite = Invite.from_code(code)
    if invite and not invite.invitee_id:
        time_since_usage = datetime.utcnow().replace(tzinfo=pytz.utc) - invite.time_sent
        if time_since_usage.total_seconds() < app.config['INVITE_LIFETIME']:
            return
    if code:
        raise APIException(f'{code} is not a valid invite code.')
    raise APIException(f'An invite code is required for registration.')
