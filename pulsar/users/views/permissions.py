import flask
from .. import bp
from ..models import User, UserPermission
from ..validators import permissions_dict
from voluptuous import Schema, Optional
from pulsar import db, APIException
from pulsar.utils import (choose_user, assert_permission, require_permission,
                          get_all_permissions, validate_data, bool_get)

app = flask.current_app

view_permissions_schema = Schema({
    Optional('all', default=False): bool_get,
    })


@bp.route('/permissions', methods=['GET'])
@bp.route('/permissions/user/<int:user_id>', methods=['GET'])
@require_permission('list_permissions')
@validate_data(view_permissions_schema)
def view_permissions(user_id=None, all=False):
    """
    View the permissions given to a user. Defaults to self if no user_id
    is provided. Requires the ``list_permissions`` permission to view
    one's own permissions list, and the ``manipulate_permissions`` permission
    to view another's permissions list. One can also view all available
    permissions, if they have the ``manipulate_permissions`` permission.

    .. :quickref: Permission; View available permissions.

    **Example request**:

    .. sourcecode:: http

       GET /permissions HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           "list_permissions",
           "manipulate_permissions",
           "change_password"
         ]
       }

    :query boolean all: Whether or not to return all available permissions

    :>json list response: A list of permission name strings

    :statuscode 200: View successful
    :statuscode 403: User lacks sufficient permissions to view permissions
    """
    if all:
        assert_permission('manipulate_permissions')
        permissions = get_all_permissions()
    else:
        user = choose_user(user_id, 'manipulate_permissions')
        permissions = user.permissions
    return flask.jsonify({'permissions': permissions})


change_permissions_schema = Schema({
    'permissions': permissions_dict,
    }, required=True)


@bp.route('/permissions/user/<int:user_id>', methods=['PUT'])
@require_permission('manipulate_permissions')
@validate_data(change_permissions_schema)
def change_permissions(user_id, permissions):
    """
    Manually change the permissions assignments of a user.
    Requires the ``manipulate_permissions`` permission.

    .. :quickref: Permission; Change assigned permissions.

    **Example request**:

    .. sourcecode:: http

       PUT /permissions HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "permissions": {
           "send_invites": true,
           "change_password": false
         }
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           "list_permissions",
           "manipulate_permissions",
           "send_invites"
         ]
       }

    :json dict permissions: A dictionary of permissions to add/remove, with
        the permission name as the key and a boolean (True = add, False = remove)
        as the value.

    :>json list response: A list of permission name strings

    :statuscode 200: Permissions successfully changed
    :statuscode 400: Attempted removal of a nonexistent permission or addition of
        an existing permission
    :statuscode 404: User lacks sufficient permissions to make a request
    """
    user = User.from_id(user_id)
    to_add, to_delete = check_permissions(user, permissions)

    for permission in to_delete:
        db.session.delete(permission)
    for perm_name in to_add:
        db.session.add(UserPermission(
            user_id=user.id,
            permission=perm_name))
    db.session.commit()

    return flask.jsonify({'permissions': user.permissions})


def check_permissions(user, permissions):
    """
    Validates that the provided permissions can be applied to the user.

    :param User user: The recipient of the permission changes.
    :param dict permissions: A dictionary of permission changes,
        with permission name and boolean (True = Add, False = Remove)
        key value pairs.
    :return: A tuple of lists, one of permissions to add and another of
        permissions to remove.
    :type: tuple
    :raises APIException: If the user already has a to-add permission or
        lacks a to-delete permission.
    """
    to_add, to_delete = [], []
    for perm_name, action in permissions.items():
        permission = UserPermission.from_attrs(user.id, perm_name)
        has_permission = user.has_permission(perm_name)
        if has_permission and not action:
            to_delete.append(permission)
        elif not has_permission and action:
            to_add.append(perm_name)
        else:
            if has_permission:
                raise APIException(
                    f'{user.username} already has the permission {perm_name}.')
            raise APIException(
                f'{user.username} does not have the permission {perm_name}.')
    return (to_add, to_delete)
