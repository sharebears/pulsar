from typing import Dict, Optional

import flask
from voluptuous import Schema

from pulsar import APIException, cache, db
from pulsar.models import User, UserPermission
from pulsar.utils import get_all_permissions, require_permission, validate_data
from pulsar.validators import check_permissions, permissions_dict

from . import bp

app = flask.current_app


@bp.route('/permissions', methods=['GET'])
@require_permission('modify_permissions')
def view_permissions(user_id: Optional[int] = None,
                     all: bool = False) -> flask.Response:
    """
    View all permissions available. Requires the ``modify_permissions`` permission.

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
           "modify_permissions",
           "change_password"
         ]
       }

    :>json list response: A list of permission name strings

    :statuscode 200: View successful
    :statuscode 403: User lacks sufficient permissions to view permissions
    """
    return flask.jsonify({'permissions': get_all_permissions()})


CHANGE_PERMISSIONS_SCHEMA = Schema({
    'permissions': permissions_dict,
    }, required=True)


@bp.route('/permissions/user/<int:user_id>', methods=['PUT'])
@require_permission('modify_permissions')
@validate_data(CHANGE_PERMISSIONS_SCHEMA)
def change_permissions(user_id: int,
                       permissions: Dict[str, bool]) -> flask.Response:
    """
    Manually change the permissions assignments of a user.
    Requires the ``modify_permissions`` permission.

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
           "modify_permissions",
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
        permission_model = UserPermission.from_attrs(user.id, permission)
        db.session.delete(permission_model)
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
    cache.delete(user.__cache_key_permissions__.format(id=user.id))

    return flask.jsonify({'permissions': user.permissions})
