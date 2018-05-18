from copy import copy
from typing import Any, Dict, List

import flask
from voluptuous import All, Length, Optional, Schema

from pulsar import APIException, db
from pulsar.models import SecondaryClass, UserClass
from pulsar.utils import require_permission, validate_data
from pulsar.validators import bool_get, permissions_dict, permissions_list

from . import bp

app = flask.current_app

secondary_schema = Schema({
    'secondary': bool_get,
    })


@bp.route('/user_classes/<int:user_class_id>', methods=['GET'])
@require_permission('modify_user_classes')
@validate_data(secondary_schema)
def view_user_class(user_class_id: int,
                    secondary: bool = False) -> flask.Response:
    """
    View an available user class and its associated permission sets.
    Requires the ``list_user_classes`` permission.

    .. :quickref: UserClass; View a user class.

    **Example request**:

    .. sourcecode:: http

       GET /user_classes/1 HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "id": 1,
           "name": "user",
           "permissions": [
             "change_password",
             "list_permissions"
           ]
         }
       }

    :query boolean secondary: Whether or not to view a secondary or primary user class

    :>jsonarr int id: The ID of the user class
    :>jsonarr string name: The name of the user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: View successful
    """
    u_class: Any = SecondaryClass if secondary else UserClass
    return flask.jsonify(u_class.from_id(
        user_class_id, _404=f'{"Secondary" if secondary else "User"} class'))


@bp.route('/user_classes', methods=['GET'])
@require_permission('list_user_classes')
@validate_data(secondary_schema)
def view_multiple_user_classes(secondary: bool = False) -> flask.Response:
    """
    View all available user classes and their associated permission sets.
    Requires the ``list_user_classes`` permission.

    .. :quickref: UserClass; View multiple user classes.

    **Example request**:

    .. sourcecode:: http

       GET /user_classes HTTP/1.1
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
           {
             "id": 1,
             "name": "User",
             "permissions": [
               "change_password",
               "list_permissions"
             ]
           },
           {
             "id": 2,
             "name": "Power User",
             "permissions": [
               "change_password",
               "list_permissions",
               "send_invites",
               "revoke_invites"
             ]
           }
         ]
       }

    :query boolean secondary: Whether or not to view secondary or primary user classes

    :>json list response: A list of user classes

    :>jsonarr int id: The ID of the user class
    :>jsonarr string name: The name of the user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: View successful
    :statuscode 404: User class does not exist
    """
    return flask.jsonify({  # type: ignore
        'user_classes': UserClass.get_all(),
        'secondary_classes': SecondaryClass.get_all(),
        })


create_user_class_schema = Schema({
    'name': All(str, Length(max=24)),
    'permissions': permissions_list,
    Optional('secondary', default=False): bool_get,
    }, required=True)


@bp.route('/user_classes', methods=['POST'])
@require_permission('modify_user_classes')
@validate_data(create_user_class_schema)
def create_user_class(name: str,
                      secondary: bool,
                      permissions: List[str]) -> flask.Response:
    """
    Create a new user class. Requires the ``modify_user_classes`` permission.

    .. :quickref: UserClass; Create new user class.

    **Example request**:

    .. sourcecode:: http

       POST /user_classes HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "name": "user_v2",
         "permissions": [
           "send_invites",
           "change_password"
         ]
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "id": 2,
           "name": "user_v2",
           "permissions": [
             "send_invites",
             "change_password"
           ]
         }
       }

    :json string name: Name of the user class
    :json list permissions: A list of permissions encoded as strings
    :json boolean secondary: Whether or not to create a secondary or primary class
        (Default False)

    :>jsonarr int id: The ID of the user class
    :>jsonarr string name: The name of the user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: User class successfully created
    :statuscode 400: User class name taken or invalid permissions
    """
    u_class: Any = SecondaryClass if secondary else UserClass
    return flask.jsonify(u_class.new(
        name=name,
        permissions=permissions))


@bp.route('/user_classes/<int:user_class_id>', methods=['DELETE'])
@require_permission('modify_user_classes')
def delete_user_class(user_class_id: int) -> flask.Response:
    """
    Create a new user class. Requires the ``modify_user_classes`` permission.

    .. :quickref: UserClass; Delete user class.

    **Example request**:

    .. sourcecode:: http

       PUT /user_classes HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "name": "user_v2"
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "User class user_v2 has been deleted."
       }

    :query boolean secondary: Whether or not to delete a secondary or primary user class

    :json string name: Name of the user class

    :>json string response: Success or failure message

    :statuscode 200: Userclass successfully deleted
    :statuscode 400: Unable to delete user class
    :statuscode 404: Userclass does not exist
    """
    # Determine secondary here because it's a query arg
    request_args: dict = flask.request.args.to_dict()
    secondary: bool = bool_get(request_args['secondary']) if 'secondary' in request_args else False
    u_class: Any = SecondaryClass if secondary else UserClass

    user_class = u_class.from_id(
        user_class_id, _404=f'{"Secondary" if secondary else "User"} class')
    if user_class.has_users():
        raise APIException(f'You cannot delete a {"secondary" if secondary else "user"} '
                           'class while users are assigned to it.')

    response = f'{"Secondary" if secondary else "User"} class {user_class.name} has been deleted.'
    db.session.delete(user_class)
    db.session.commit()
    return flask.jsonify(response)


modify_user_class_schema = Schema({
    'permissions': permissions_dict,
    Optional('secondary', default=False): bool_get,
    }, required=True)


@bp.route('/user_classes/<int:user_class_id>', methods=['PUT'])
@require_permission('modify_user_classes')
@validate_data(modify_user_class_schema)
def modify_user_class(user_class_id: int,
                      permissions: Dict[str, bool],
                      secondary: bool) -> flask.Response:
    """
    Modifies permissions for an existing user class.
    Requires the ``modify_user_classes`` permission.

    .. :quickref: UserClass; Modify existing user class.

    **Example request**:

    .. sourcecode:: http

       PUT /user_classes/user HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "permissions": {
           "send_invites": false,
           "change_password": true,
           "list_permissions": true
         }
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
           "name": "User",
           "permissions": [
             "change_password",
             "list_permissions"
           ]
         }
       }

    :>json dict permissions: A dictionary of permissions to add/remove, with
        the permission name as the key and a boolean (True = add, False = remove)
        as the value.
    :>json boolean secondary: Whether or not to modify a secondary or primary user class

    :>jsonarr int id: The ID of the user class
    :>jsonarr string name: The name of the user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: Userclass successfully modified
    :statuscode 400: Permissions cannot be applied
    :statuscode 404: Userclass does not exist
    """
    c_name: str = f'{"Secondary" if secondary else "User"} class'
    u_class: Any = SecondaryClass if secondary else UserClass
    user_class: 'UserClass' = u_class.from_id(user_class_id, _404=c_name)

    uc_perms = copy(user_class.permissions)
    to_add = {p for p, a in permissions.items() if a is True}
    to_delete = {p for p, a in permissions.items() if a is False}

    for perm in to_add:
        if perm in uc_perms:
            raise APIException(f'{c_name} {user_class.name} already has the permission {perm}.')
        uc_perms.append(perm)
    for perm in to_delete:
        if perm not in uc_perms:
            raise APIException(f'{c_name} {user_class.name} does not have the permission {perm}.')
        uc_perms.remove(perm)

    # Permissions don't update if list reference doesn't change.
    # (This is also why uc_perms was copied from user_class.permissions)
    user_class.permissions = uc_perms
    db.session.commit()
    return flask.jsonify(user_class)
