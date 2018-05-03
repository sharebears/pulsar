import flask
from voluptuous import Invalid


def permissions_list(val):
    """
    Takes a list of items and asserts that all of them are in the permissions list of
    a user.
    """
    if isinstance(val, list):
        for perm in val:
            if perm not in flask.g.user.permissions:
                break
        else:
            return val
    raise Invalid('permissions must be in the user\'s permissions list')
