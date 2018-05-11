import flask
from functools import wraps
from werkzeug import find_modules, import_string
from pulsar import _404Exception, _403Exception
from pulsar.models import User

app = flask.current_app


def require_permission(permission, masquerade=False):
    """
    Requires a user to have the specified permission to access the view function.

    :param str permission: The permission required to access the API endpoint.
    :param bool masquerade: Whether or not to disguise the failed view attempt as
        a 404.

    :raises _403Exception: If the user does not exist or does not have enough
        permission to view the resource. Locked accounts are given a different message.
        This can be masqueraded as a 404.
    :raises _403Exception: If an API Key is used and does not have enough permissions to
        access the resource.
    """
    def wrapper(func):
        @wraps(func)
        def new_function(*args, **kwargs):
            if not flask.g.user:
                raise _403Exception(masquerade=True)

            if not flask.g.user.has_permission(permission):
                if flask.g.user.locked and not masquerade:
                    raise _403Exception(message='Your account has been locked.')
                raise _403Exception(masquerade=masquerade)

            if flask.g.api_key and not flask.g.api_key.has_permission(permission):
                raise _403Exception(message='This API Key does not have permission to '
                                    'access this resource.')
            return func(*args, **kwargs)
        return new_function
    return wrapper


def get_all_permissions():
    """
    Aggregate all the permissions listed in module __init__ files by iterating
    through them and adding their PERMISSIONS attr to a list.
    Restrict all uses of this function to users with the "get_all_permissions" permission.
    Returns the list of aggregated permissions.
    """
    permissions = []
    for name in find_modules('pulsar', include_packages=True):
        mod = import_string(name)
        if hasattr(mod, 'PERMISSIONS') and isinstance(mod.PERMISSIONS, list):
            permissions += mod.PERMISSIONS
    return permissions


def choose_user(user_id, permission):
    """
    Takes a user_id and a permission. If the user_id is specified, the user with that
    user id is fetched and then returned if the requesting user has the given permission.
    Otherwise, the requester's user is returned. This function needs to be behind a
    ``@require_permission`` decorated view.

    :param int user_id: The user_id of the requested user.
    :param str permission: The permission needed to get the other user's user object.

    :raises _403Exception: The requesting user does not have the specified permission.
    :raises _404Exception: The requested user does not exist.
    """
    if user_id and flask.g.user.id != user_id:
        if flask.g.user.has_permission(permission):
            user = User.from_id(user_id)
            if user:
                return user
            raise _404Exception(f'User {user_id}')
        raise _403Exception
    return flask.g.user


def assert_user(user_id, permission=None):
    """
    Assert that a user_id belongs to the requesting user, or that
    the requesting user has a given permission.
    """
    return (flask.g.user.id == user_id or flask.g.user.has_permission(permission))


def assert_permission(permission, masquerade=False):
    "Assert that the requesting user has a permission, raise a 403 if they do not."
    if not flask.g.user.has_permission(permission):
        raise _403Exception if not masquerade else _404Exception
