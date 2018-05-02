import re
import pytz
import flask
from datetime import datetime
from sqlalchemy import func
from voluptuous import Invalid
from .models import User
from pulsar.utils import USERNAME_REGEX, get_all_permissions
from pulsar.invites.models import Invite

app = flask.current_app


def permissions_dict(val):
    permissions = get_all_permissions()
    if isinstance(val, dict):
        for perm_name, action in val.items():
            if perm_name not in permissions:
                raise Invalid(f'{perm_name} is not a valid permission')
            elif not isinstance(action, bool):
                raise Invalid('permission actions must be booleans')
    else:
        raise Invalid('input value must be a dictionary')
    return val


def val_username(username):
    """
    Ensures that a username is not taken by comparing it with existing DB results.

    :param str username: Username to check and verify
    :return: An unused username, same as input (``str``)
    :raises Invalid: If the username does not meet length requirements
        or is already used by another user
    """
    if (not isinstance(username, str)
            or not re.match(USERNAME_REGEX, username)
            or len(username) > 32):
        raise Invalid('usernames must start with an alphanumeric '
                      'character; can only contain alphanumeric characters, '
                      'underscores, hyphens, and periods; and be 32 characters '
                      'or less')

    username = username.lower()
    if (User.query.filter(func.lower(User.username) == username).one_or_none()):
        raise Invalid(f'another user already has the username {username}')
    return username


def val_invite_code(code):
    """
    Check an invite code against existing invite codes;
    Raises an APIException if the code isn't valid.

    :param str code: Invite code to check and verify
    :return: An invite code (``str``) or, if site is open registration, ``None``
    :raises Invalid: The invite code cannot be used
    """
    if not app.config['REQUIRE_INVITE_CODE']:
        return None

    if code is not None and not isinstance(code, str):
        raise Invalid('code must be a string')

    invite = Invite.from_code(code)
    if invite and not invite.invitee_id:
        time_since_usage = datetime.utcnow().replace(tzinfo=pytz.utc) - invite.time_sent
        if time_since_usage.total_seconds() < app.config['INVITE_LIFETIME']:
            return code

    if code:
        raise Invalid(f'{code} is not a valid invite code')
    raise Invalid(f'an invite code is required for registration')
