import flask
from functools import wraps
from werkzeug import find_modules, import_string
from pulsar import _404Exception, _403Exception
from pulsar.users.models import User

app = flask.current_app


def require_auth(func):
    """
    If the site is private, this decorator requires that flask.g.user exist.
    If the site is public, nothing happens.
    Note: flask.g.user can be None with this decorator, unlike in require_permission.
    """
    @wraps(func)
    def new_function(*args, **kwargs):
        if app.config['SITE_PRIVATE'] and not flask.g.user:
            raise _403Exception(masquerade=True)
        return func(*args, **kwargs)
    return new_function


def require_permission(permission):
    """
    Require a user to have a specified permission to view the resource,
    otherwise a 404 Exception is raised.
    If the user does not exist (no authentication), a 403 Exception
    is raised (runs 403 notifications), but it masquerades as a 404 Exception to the user.
    """
    def wrapper(func):
        @wraps(func)
        def new_function(*args, **kwargs):
            if not flask.g.user or not flask.g.user.has_permission(permission):
                raise _403Exception(masquerade=True)
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


def choose_user(user_id, permission=None):
    """
    Takes a user_id and an optional permission. If the user_id is specified,
    the user with that user id is fetched and then returned if the requesting user
    has the given permission. Otherwise, the requester's user is returned.
    This function needs to be behind a @require_permission view.
    Raises a 403 Exception if the requesting user does not have the specified permission.
    Raises a 404 Exception if the requested user does not exist.
    """
    if user_id and flask.g.user.id != user_id:
        if permission and flask.g.user.has_permission(permission):
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
