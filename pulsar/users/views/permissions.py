import flask
from . import bp
from ..models import User, Permission
from voluptuous import Schema, Optional
from pulsar import db, APIException
from pulsar.utils import (choose_user, assert_permission, require_permission,
                          get_all_permissions, validate_data, bool_get,
                          permissions_dict)

app = flask.current_app

view_permissions_schema = Schema({
    Optional('all', default=False): bool_get,
    })

change_permissions_schema = Schema({
    'permissions': permissions_dict,
    }, required=True)


@bp.route('/permissions', methods=['GET'])
@bp.route('/permissions/user/<int:user_id>', methods=['GET'])
@require_permission('list_permissions')
@validate_data(view_permissions_schema)
def view_permissions(user_id=None, all=False):
    if all:
        assert_permission('manipulate_permissions')
        permissions = get_all_permissions()
    else:
        user = choose_user(user_id, 'manipulate_permissions')
        permissions = [perm.permission for perm in user.permissions]
    return flask.jsonify({'permissions': permissions})


@bp.route('/permissions/user/<int:user_id>', methods=['PUT'])
@require_permission('manipulate_permissions')
@validate_data(change_permissions_schema)
def change_permissions(user_id, permissions):
    user = User.from_id(user_id)
    to_add, to_delete = check_permissions(user, permissions)

    for permission in to_delete:
        db.session.delete(permission)
    for perm_name in to_add:
        db.session.add(Permission(
            user_id=user.id,
            permission=perm_name))
    db.session.commit()

    return flask.jsonify({'permissions': [perm.permission for perm in user.permissions]})


def check_permissions(user, permissions):
    to_add, to_delete = [], []
    for perm_name, action in permissions.items():
        permission = user.has_permission(perm_name)
        if permission and not action:
            to_delete.append(permission)
        elif not permission and action:
            to_add.append(perm_name)
        else:
            if permission:
                raise APIException(
                    f'{user.username} already has the permission {perm_name}.')
            raise APIException(
                f'{user.username} does not have the permission {perm_name}.')
    return (to_add, to_delete)
