import flask
from collections import defaultdict
from voluptuous import Invalid
from pulsar import APIException
from pulsar.models import UserClass, UserPermission
from pulsar.utils import get_all_permissions


def permissions_list(perm_list):
    """
    Validates that every permission in the list is a valid permission.

    :param list perm_list: A list of permissions encoded as ``str``

    :return: The input ``perm_list``
    :raises Invalid: If a permission in the list isn't valid, or input isn't a list
    """
    permissions = get_all_permissions()
    invalid = []
    if isinstance(perm_list, list):
        for perm in perm_list:
            if perm not in permissions:
                invalid.append(perm)
    else:
        raise Invalid('Permissions must be in a list,')
    if invalid:
        raise Invalid(f'The following permissions are invalid: {", ".join(invalid)},')
    return perm_list


def permissions_list_of_user(perm_list):
    """
    Takes a list of items and asserts that all of them are in the permissions list of
    a user.

    :param list perm_list: A list of permissions encoded as ``str``

    :return: The input ``perm_list``
    :raises Invalid: If the user does not have a permission in the list
    """
    if isinstance(perm_list, list):
        for perm in perm_list:
            if perm not in flask.g.user.permissions:
                break
        else:
            return perm_list
    raise Invalid('permissions must be in the user\'s permissions list')


def permissions_dict(val):
    """
    Validates that a dictionary contains valid permission name keys
    and has boolean values.

    :param dict val: Dictionary of permissions and booleans

    :return: Input ``val``
    :raises Invalid: A permission name is invalid or a value isn't a bool
    """
    permissions = get_all_permissions()
    if isinstance(val, dict):
        for perm_name, action in val.items():
            if not isinstance(action, bool):
                raise Invalid('permission actions must be booleans')
            elif perm_name not in permissions and action is True:
                # Do not disallow removal of non-existent permissions.
                raise Invalid(f'{perm_name} is not a valid permission')
    else:
        raise Invalid('input value must be a dictionary')
    return val


def check_permissions(user, permissions):
    """
    Validates that the provided permissions can be applied to the user.
    Permissions can be added if they were previously taken away or aren't
    a permission given to the user class. Permissions can be removed if
    were specifically given to the user previously, or are included in their userclass.

    :param User user: The recipient of the permission changes.
    :param dict permissions: A dictionary of permission changes, with
        permission name and boolean (True = Add, False = Remove) key value pairs.
    :return: A tuple of lists, one of permissions to add, another with
        permissions to ungrant, and another of permissions to remove.
    :type: tuple
    :raises APIException: If the user already has a to-add permission or
        lacks a to-delete permission.
    """
    add, ungrant, delete, errors = [], [], [], defaultdict(list)
    uc_permissions = user.user_class.permissions
    user_permissions = UserPermission.from_user(user.id)

    for perm, active in permissions.items():
        if active is True:
            if perm in user_permissions:
                if user_permissions[perm] is False:
                    delete.append(perm)
                    add.append(perm)
                else:
                    errors['add'].append(perm)
            elif perm not in uc_permissions:
                add.append(perm)
            else:
                errors['add'].append(perm)
        else:
            if perm in user_permissions:
                if user_permissions[perm] is True:
                    delete.append(perm)
                    if perm in uc_permissions:
                        ungrant.append(perm)
                else:
                    errors['delete'].append(perm)
            elif perm in uc_permissions:
                ungrant.append(perm)
            else:
                errors['delete'].append(perm)

    if errors:
        message = []
        if 'add' in errors:
            message.append('The following permissions could not be added: {}.'.format(
                ", ".join(errors['add'])))
        if 'delete' in errors:
            message.append('The following permissions could not be deleted: {}.'.format(
                ", ".join(errors['delete'])))
        raise APIException(' '.join(message))

    return (add, ungrant, delete)
