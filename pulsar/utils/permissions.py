from functools import wraps
from typing import Callable, List, Optional

import flask
from werkzeug import find_modules, import_string

from pulsar import _312Exception, _401Exception, _403Exception, _404Exception

app = flask.current_app


def require_permission(permission: str,
                       masquerade: bool = False) -> Callable:
    """
    Requires a user to have the specified permission to access the view function.

    :param permission:     The permission required to access the API endpoint
    :param masquerade:     Whether or not to disguise the failed view attempt as a 404

    :raises _403Exception: If the user does not exist or does not have enough
                           permission to view the resource. Locked accounts are
                           given a different message. This can be masqueraded as a 404
    :raises _403Exception: If an API Key is used and does not have enough permissions to
                           access the resource
    """
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        def new_function(*args, **kwargs) -> Callable:
            if not flask.g.user:
                raise _401Exception

            if not flask.g.user.has_permission(permission):
                if flask.g.user.locked and not masquerade:
                    raise _312Exception(lock=True)
                raise _403Exception(masquerade=masquerade)

            if flask.g.api_key and not flask.g.api_key.has_permission(permission):
                raise _403Exception(message='This APIKey does not have permission to '
                                    'access this resource.')
            return func(*args, **kwargs)
        return new_function
    return wrapper


def get_all_permissions() -> List[str]:
    """
    Aggregate all the permissions listed in module __init__ files by iterating
    through them and adding their PERMISSIONS attr to a list.
    Restrict all uses of this function to users with the "get_all_permissions" permission.
    Returns the list of aggregated permissions

    :return: The list of permissions
    """
    permissions: List[str] = []
    for name in find_modules('pulsar', include_packages=True):
        mod = import_string(name)
        if hasattr(mod, 'PERMISSIONS') and isinstance(mod.PERMISSIONS, list):
            permissions += mod.PERMISSIONS
    return permissions


def choose_user(user_id: Optional[int],
                permission: str):  # -> User
    """
    Takes a user_id and a permission. If the user_id is specified, the user with that
    user id is fetched and then returned if the requesting user has the given permission.
    Otherwise, the requester's user is returned. This function needs to be behind a
    ``@require_permission`` decorated view.

    :param user_id:        The user_id of the requested user.
    :param permission:     The permission needed to get the other user's user object.

    :return:               The chosen user
    :raises _403Exception: The requesting user does not have the specified permission
    :raises _404Exception: The requested user does not exist
    """
    from pulsar.users.models import User
    if user_id and flask.g.user.id != user_id:
        if flask.g.user.has_permission(permission):
            user = User.from_pk(user_id)
            if user:
                return user
            raise _404Exception(f'User {user_id}')
        raise _403Exception
    return flask.g.user


def assert_user(user_id: int,
                permission: Optional[str] = None) -> bool:
    """
    Assert that a user_id belongs to the requesting user, or that
    the requesting user has a given permission.
    """
    return (flask.g.user.id == user_id or flask.g.user.has_permission(permission))


def assert_permission(permission: str,
                      masquerade: bool = False) -> None:
    "Assert that the requesting user has a permission, raise a 403 if they do not."
    if not flask.g.user.has_permission(permission):
        if masquerade:
            raise _404Exception
        raise _403Exception
