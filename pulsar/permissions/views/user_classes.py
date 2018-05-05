import flask
from copy import copy
from sqlalchemy import func
from .. import bp
from ..models import UserClass
from ..schemas import user_class_schema, multiple_user_class_schema
from ..validators import val_unique_user_class, permissions_list, permissions_dict
from voluptuous import Schema
from pulsar import db, APIException, _404Exception
from pulsar.utils import require_permission, validate_data
from pulsar.users.models import User

app = flask.current_app


@bp.route('/user_classes/<user_class_name>', methods=['GET'])
@require_permission('list_user_classes')
def view_user_class(user_class_name):
    """
    View an available user class and its associated permission sets.
    Requires the ``list_user_classes`` permission.

    .. :quickref: UserClass; View a user class.

    **Example request**:

    .. sourcecode:: http

       GET /user_classes/user HTTP/1.1
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
           "user_class": "user",
           "permissions": [
             "change_password",
             "list_permissions"
           ]
         }
       }

    :>jsonarr string user_class: The name of a user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: View successful
    """
    user_class = UserClass.from_name(user_class_name)
    if user_class:
        return user_class_schema.jsonify(user_class)
    raise _404Exception(f'User class {user_class_name}')


@bp.route('/user_classes', methods=['GET'])
@require_permission('list_user_classes')
def view_user_classes():
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
             "user_class": "user",
             "permissions": [
               "change_password",
               "list_permissions"
             ]
           },
           {
             "user_class": "power user",
             "permissions": [
               "change_password",
               "list_permissions",
               "send_invites",
               "revoke_invites"
             ]
           }
         ]
       }

    :>json list response: A list of user classes

    :>jsonarr string user_class: The name of a user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: View successful
    :statuscode 404: User class does not exist
    """
    user_classes = UserClass.get_all()
    return multiple_user_class_schema.jsonify(user_classes)


create_user_class_schema = Schema({
    'user_class': val_unique_user_class,
    'permissions': permissions_list,
    }, required=True)


@bp.route('/user_classes', methods=['POST'])
@require_permission('modify_user_classes')
@validate_data(create_user_class_schema)
def create_user_class(user_class, permissions):
    """
    Create a new user class. Requires the ``modify_user_classes`` permission.

    .. :quickref: UserClass; Create new userclass.

    **Example request**:

    .. sourcecode:: http

       POST /user_classes HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "user_class": "user_v2",
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
           "user_class": "user_v2",
           "permissions": [
             "send_invites",
             "change_password"
           ]
         }
       }

    :json string user_class: Name of the user class
    :json list permissions: A list of permissions encoded as strings

    :>jsonarr string user_class: The name of a user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: User class successfully created
    :statuscode 400: User class name taken or invalid permissions
    """
    user_class = UserClass(
        user_class=user_class,
        permissions=permissions,
        )
    db.session.add(user_class)
    db.session.commit()
    return user_class_schema.jsonify(user_class)


@bp.route('/user_classes/<user_class_name>', methods=['DELETE'])
@require_permission('modify_user_classes')
def delete_user_class(user_class_name):
    """
    Create a new user class. Requires the ``modify_user_classes`` permission.

    .. :quickref: UserClass; Create new userclass.

    **Example request**:

    .. sourcecode:: http

       PUT /user_classes HTTP/1.1
       Host: pul.sar
       Accept: application/json

       {
         "user_class": "user_v2"
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

    :json string user_class: Name of the user class

    :>json string response: Success or failure message

    :statuscode 200: Userclass successfully deleted
    :statuscode 400: Unable to delete userclass
    :statuscode 404: Userclass does not exist
    """
    user_class = UserClass.from_name(user_class_name)
    if not user_class:
        raise _404Exception(f'User class {user_class_name}')
    if db.session.query(User.id).filter(
            func.lower(User.user_class) == user_class_name.lower()
            ).limit(1).first():
        raise APIException(
            'You cannot delete a user class while users are assigned to it.')

    response = f'User class {user_class.user_class} has been deleted.'
    db.session.delete(user_class)
    db.session.commit()
    return flask.jsonify(response)


modify_user_class_schema = Schema({
    'permissions': permissions_dict,
    }, required=True)


@bp.route('/user_classes/<user_class_name>', methods=['PUT'])
@require_permission('modify_user_classes')
@validate_data(modify_user_class_schema)
def modify_user_class(user_class_name, permissions):
    """
    Modifies permissions for an existing user class.
    Requires the ``modify_user_classes`` permission.

    .. :quickref: UserClass; Modify existing userclass.

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
           "user_class": "user",
           "permissions": [
             "change_password",
             "list_permissions"
           ]
         }
       }

    :json dict permissions: A dictionary of permissions to add/remove, with
        the permission name as the key and a boolean (True = add, False = remove)
        as the value.

    :>jsonarr string user_class: The name of a user class
    :>jsonarr list permissions: A list of permissions, encoded as strings,
        assigned to that user class

    :statuscode 200: Userclass successfully modified
    :statuscode 400: Permissions cannot be applied
    :statuscode 404: Userclass does not exist
    """
    user_class = UserClass.from_name(user_class_name)
    if not user_class:
        raise _404Exception(f'User class {user_class_name}')

    uc_perms = copy(user_class.permissions)
    to_add = {p for p, a in permissions.items() if a is True}
    to_delete = {p for p, a in permissions.items() if a is False}

    for perm in to_add:
        if perm in uc_perms:
            raise APIException(f'User class {user_class.user_class} '
                               f'already has the permission {perm}.')
        uc_perms.append(perm)
    for perm in to_delete:
        if perm not in uc_perms:
            raise APIException(f'User class {user_class.user_class} '
                               f'does not have the permission {perm}.')
        uc_perms.remove(perm)

    # Permissions don't update if list reference doesn't change.
    # (This is also why uc_perms was copied from user_class.permissions)
    user_class.permissions = uc_perms
    db.session.commit()
    return user_class_schema.jsonify(user_class)
