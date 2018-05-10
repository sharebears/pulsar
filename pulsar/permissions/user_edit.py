import flask
from . import bp
from .models import UserPermission
from .validators import permissions_dict, check_permissions
from voluptuous import Schema, Optional
from pulsar import db, APIException
from pulsar.users.models import User
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

       PUT /permissions/user/1 HTTP/1.1
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
    to_add, to_ungrant, to_delete = check_permissions(user, permissions)

    # Validate that ungrant permissions all exist, since permissions_dict doesn't.
    existing_permissions = get_all_permissions()
    for p in to_ungrant:
        if p not in existing_permissions:
            raise APIException(f'{p} is not a valid permission.')

    for permission in to_delete:
        permission = UserPermission.from_attrs(user.id, permission)
        db.session.delete(permission)
    db.session.commit()
    for perm_name in to_add:
        db.session.add(UserPermission(
            user_id=user.id,
            permission=perm_name))
    for perm_name in to_ungrant:
        db.session.add(UserPermission(
            user_id=user.id,
            permission=perm_name,
            granted=False))
    db.session.commit()

    return flask.jsonify({'permissions': user.permissions})
