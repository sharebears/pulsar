from typing import Dict, Set, Type, Union

import flask
from voluptuous import All, Email, Range, Schema
from voluptuous.validators import Match

from pulsar import APIException, cache, db
from pulsar.permissions.models import ForumPermission, UserPermission
from pulsar.users.models import User
from pulsar.utils import get_all_permissions, require_permission, validate_data
from pulsar.validators import (PASSWORD_REGEX, ForumPermissionsDict, PermissionsDict,
                               check_permissions)

from . import bp

app = flask.current_app

MODERATE_USER_SCHEMA = Schema({
    'email': Email(),
    'password': Match(PASSWORD_REGEX, msg=(
        'Password must be between 12 and 512 characters and contain at least 1 letter, '
        '1 number, and 1 special character')),
    'uploaded': All(int, Range(min=0, max=9223372036854775808)),
    'downloaded': All(int, Range(min=0, max=9223372036854775808)),
    'invites': All(int, Range(min=0, max=2147483648)),
    'permissions': PermissionsDict(restrict='moderate_users_advanced'),
    'forum_permissions': ForumPermissionsDict,
    })


@bp.route('/users/<int:user_id>/moderate', methods=['PUT'])
@require_permission('moderate_users')
@validate_data(MODERATE_USER_SCHEMA)
def moderate_user(user_id: int,
                  email: str = None,
                  password: str = None,
                  uploaded: int = None,
                  downloaded: int = None,
                  invites: int = None,
                  permissions: Dict[str, bool] = None,
                  forum_permissions: Dict[str, bool] = None) -> flask.Response:
    """
    Moderate a user - change password for them, alter stats, modify basic permissions,
    etc.

    .. :quickref: User; Moderate user.

    **Example request**:

    .. sourcecode:: http

       PUT /users/1/moderate HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "password": "an-ev3n-be77er-pa$$w0rd"
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
           "email": "lights@pul.sar"
         }
       }

    :json string password: User's new password. Must be 12+ characters and contain
        at least one letter, one number, and one special character.

    :>json string response: Success message

    :statuscode 200: User successfully moderated
    :statuscode 400: User unsuccessfully moderated
    :statuscode 403: User does not have permission to moderate some parts of user
    """
    user = User.from_pk(user_id, _404=True)

    if password:
        user.set_password(password)
    if email:
        user.email = email
    if uploaded:
        user.uploaded = uploaded
    if downloaded:
        user.downloaded = downloaded
    if invites:
        user.invites = invites
    if permissions:
        change_user_permissions(user, permissions)
    if forum_permissions:
        change_forum_permissions(user, forum_permissions)

    db.session.commit()
    return flask.jsonify(user)


def change_user_permissions(user: User,
                            permissions: Dict[str, bool]) -> None:
    """
    Change the permissions belonging to a user. Permissions can be
    added to a user, deleted from a user, and ungranted from a user.
    Adding a permission occurs when the user does not have the specified
    permission, through custom or userclass. There are two types of permission
    removal: deletion and ungranting. Deletion ocrurs when the user has the
    permission through custom, while ungranting occurs when the user has the
    permission through userclass. If they have both custom and userclass, they
    will lose both.

    :param user:          The user to change permissions for
    :param permissions:   The permissions to change

    :raises APIException: Invalid permissions to change
    """
    to_add, to_ungrant, to_delete = check_permissions(
        user, permissions, perm_model=UserPermission, perm_attr='permissions')
    existing_permissions = get_all_permissions()
    for p in to_ungrant:
        if p not in existing_permissions:
            raise APIException(f'{p} is not a valid permission.')
    alter_permissions(UserPermission, user, to_add, to_ungrant, to_delete)
    cache.delete(user.__cache_key_permissions__.format(id=user.id))
    user.del_property_cache('permissions')


def change_forum_permissions(user: User,
                             permissions: Dict[str, bool]) -> None:
    """
    Change the forum permissions belonging to a user. Permissions can be
    added to a user, deleted from a user, and ungranted from a user.
    Adding a permission occurs when the user does not have the specified
    permission, through custom or userclass. There are two types of permission
    removal: deletion and ungranting. Deletion ocrurs when the user has the
    permission through custom, while ungranting occurs when the user has the
    permission through userclass. If they have both custom and userclass, they
    will lose both.

    :param user:          The user to change permissions for
    :param permissions:   The forum permissions to change

    :raises APIException: Invalid forum permissions to change
    """
    to_add, to_ungrant, to_delete = check_permissions(
        user, permissions, perm_model=ForumPermission, perm_attr='forum_permissions')
    alter_permissions(ForumPermission, user, to_add, to_ungrant, to_delete)
    cache.delete(user.__cache_key_forum_permissions__.format(id=user.id))
    user.del_property_cache('forum_permissions')


def alter_permissions(perm_model: Union[Type[ForumPermission], Type[UserPermission]],
                      user: User,
                      to_add: Set[str],
                      to_ungrant: Set[str],
                      to_delete: Set[str]) -> None:
    """
    Apply the permission changes to the database. The permission model to
    apply the changes to is passed as a parameter.

    :param perm_model: The permissions model, must inherit PermissionMixin
    :param user:       The user to apply the permissions to
    :param to_add:     The permissions to add
    :param to_ungrant: The permissions to ungrant
    :param to_delete:  The permissions to delete
    """
    for permission in to_delete:
        model: Union[ForumPermission, UserPermission] = perm_model.from_attrs(
            user_id=user.id,
            permission=permission)
        db.session.delete(model)
    db.session.commit()
    for perm_name in to_add:
        db.session.add(perm_model(
            user_id=user.id,
            permission=perm_name))
    for perm_name in to_ungrant:
        db.session.add(perm_model(
            user_id=user.id,
            permission=perm_name,
            granted=False))
    db.session.commit()
