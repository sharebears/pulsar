import re
from datetime import datetime
from typing import Optional

import flask
import pytz
from voluptuous import Invalid

from pulsar import APIException
from pulsar.invites.models import Invite
from pulsar.users.models import User

app = flask.current_app

USERNAME_REGEX = r'^[A-Za-z0-9][A-Za-z0-9_\-\.]*$'
PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&\^]).{12,512}$'


def ValUsername(username: str) -> str:
    """
    Ensures that a username is not taken by comparing it with existing DB results.

    :param username: Username to check and verify

    :return:         An unused username, same as input
    :raises Invalid: If the username does not meet length requirements or is
                     already used by another user
    """
    if (not isinstance(username, str)
            or not re.match(USERNAME_REGEX, username)
            or len(username) > 32
            or username == '0'  # No 0 or 1 for Gazelle compatibility.
            or username == '1'):
        raise Invalid('usernames must start with an alphanumeric '
                      'character; can only contain alphanumeric characters, '
                      'underscores, hyphens, and periods; and be 32 characters '
                      'or less')

    if User.from_username(username):
        raise Invalid(f'another user already has the username {username}')
    return username


def ValInviteCode(code: Optional[str]) -> None:
    """
    Check an invite code against existing invite codes;
    Raises an APIException if the code isn't valid.

    :param code:          Invite code to check and verify

    :return:              An invite code or, if site is open registration, ``None``
    :raises APIException: The invite code cannot be used
    """
    if not app.config['REQUIRE_INVITE_CODE']:
        return

    if code is not None and (not isinstance(code, str) or len(code) != 24):
        raise APIException('Invite code must be a 24 character string.')

    invite = Invite.from_pk(code)
    if invite and not invite.invitee_id:
        time_since_usage = datetime.utcnow().replace(tzinfo=pytz.utc) - invite.time_sent
        if time_since_usage.total_seconds() < app.config['INVITE_LIFETIME']:
            return

    if code:
        raise APIException(f'{code} is not a valid invite code.')
    raise APIException('An invite code is required for registration.')
