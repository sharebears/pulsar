import flask
from voluptuous import Invalid


def permissions_list(val):
    """
    Takes a list of items and asserts that all of them are in the permissions list of
    a user.
    """
    if isinstance(val, list):
        user_permissions = [perm.permission for perm in flask.g.user.permissions]
        for perm in val:
            if perm not in user_permissions:
                break
        else:
            return val
    raise Invalid('permissions must be in the user\'s permissions list')
