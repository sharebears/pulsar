import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Type, Union

import flask
from voluptuous import Invalid

from pulsar import APIException
from pulsar.forums.models import ForumPermission
from pulsar.permissions import BASIC_PERMISSIONS
from pulsar.permissions.models import SecondaryClass, UserPermission
from pulsar.users.models import User
from pulsar.utils import get_all_permissions

FORUM_PERMISSION = re.compile(r'forums_forums_permission_\d+')
THREAD_PERMISSION = re.compile(r'forums_threads_permission_\d+')


def permissions_list(perm_list: List[str]) -> List[str]:
    """
    Validates that every permission in the list is a valid permission.

    :param perm_list: A list of permissions encoded as ``str``

    :return:          The inputted perm_list
    :raises Invalid:  If a permission in the list isn't valid or input isn't a list
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


def permissions_list_of_user(perm_list: List[str]) -> List[str]:
    """
    Takes a list of items and asserts that all of them are in the permissions list of
    a user.

    :param perm_list: A list of permissions encoded as ``str``

    :return:          The input perm_list
    :raises Invalid:  If the user does not have a permission in the list
    """
    if isinstance(perm_list, list):
        for perm in perm_list:
            if not flask.g.user.has_permission(perm):
                break
        else:
            return perm_list
    raise Invalid('permissions must be in the user\'s permissions list')


class PermissionsDict:
    """
    Validates that a dictionary contains valid permission name keys
    and has boolean values. The available permissions can be restricted
    to the BASIC_PERMISSIONS if a permission is passed. If the requesting
    user does not have that permission, they will be restricted to the
    BASIC_PERMISSIONS.
    """

    def __init__(self, restrict: str = None) -> None:
        self.restrict = restrict

    def __call__(self, permissions: dict) -> dict:
        """
        :param permissions:    Dictionary of permissions and booleans

        :return:               The input value
        :raises Invalid:       A permission name is invalid or a value isn't a bool
        """
        permissioned = self.restrict is None or flask.g.user.has_permission(self.restrict)
        all_permissions = get_all_permissions() if permissioned else BASIC_PERMISSIONS

        if isinstance(permissions, dict):
            for perm_name, action in permissions.items():
                if not isinstance(action, bool):
                    raise Invalid('permission actions must be booleans')
                elif perm_name not in all_permissions and (action is True or not permissioned):
                    # Do not disallow removal of non-existent permissions.
                    raise Invalid(f'{perm_name} is not a valid permission')
        else:
            raise Invalid('input value must be a dictionary')
        return permissions


def ForumPermissionsDict(value):
    """
    Validate that the dictionary contains valid forum permissions as keys and
    booleans as the values.

    :param value:   The input dictionary to validate

    :return:        The input value
    :raise Invalid: If the input dictionary is not valid
    """
    if isinstance(value, dict):
        for key, val in value.items():
            if not (isinstance(key, str) and isinstance(val, bool) and (
                    FORUM_PERMISSION.match(key) or THREAD_PERMISSION.match(key))):
                break
        else:
            return value
    raise Invalid('data must be a dict with valid forums permission keys and boolean values')


def check_permissions(user: User,  # noqa: C901 (McCabe complexity)
                      permissions: Dict[str, bool],
                      perm_model: Union[Type[UserPermission], Type[ForumPermission]],
                      perm_attr: str
                      ) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    The abstracted meat of the user and forum permission checkers. Takes the input
    and some model-specific information and returns permission information.

    :param user:        The recipient of the permission changes
    :param permissions: A dictionary of permission changes, with permission name
                        and boolean (True = Add, False = Remove) key value pairs
    :param perm_model:  The permission model to be checked
    :param perm_attr:   The attribute of the user classes which represents the permissions
    """
    add: Set[str] = set()
    ungrant: Set[str] = set()
    delete: Set[str] = set()
    errors: Dict[str, Set[str]] = defaultdict(set)

    uc_permissions: Set[str] = set(getattr(user.user_class_model, perm_attr))
    for class_ in SecondaryClass.from_user(user.id):
        uc_permissions |= set(getattr(class_, perm_attr))
    custom_permissions: Dict[str, bool] = perm_model.from_user(user.id)

    for perm, active in permissions.items():
        if active is True:
            if perm in custom_permissions:
                if custom_permissions[perm] is False:
                    delete.add(perm)
                    add.add(perm)
            elif perm not in uc_permissions:
                add.add(perm)
            if perm not in add.union(delete):
                errors['add'].add(perm)
        else:
            if perm in custom_permissions and custom_permissions[perm] is True:
                delete.add(perm)
            if perm in uc_permissions:
                ungrant.add(perm)
            if perm not in delete.union(ungrant):
                errors['delete'].add(perm)

    if errors:
        message = []
        if 'add' in errors:
            message.append(f'The following {perm_model.__name__}s could not be added: '
                           f'{", ".join(errors["add"])}.')
        if 'delete' in errors:
            message.append(f'The following {perm_model.__name__}s could not be deleted: '
                           f'{", ".join(errors["delete"])}.')
        raise APIException(' '.join(message))

    return add, ungrant, delete
