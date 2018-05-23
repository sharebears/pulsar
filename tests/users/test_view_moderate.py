import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.permissions.models import UserPermission, ForumPermission
from pulsar.users.models import User


def test_int_overflow(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'invites': 99999999999999999999999999,
        }))
    check_json_response(response, 'Invalid data: value must be at most 2147483648 (key "invites")')


def test_moderate_user(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/2/moderate', data=json.dumps({
        'email': 'new@ema.il',
        'uploaded': 999,
        'downloaded': 998,
        'invites': 100,
        }))
    check_json_response(response, {
        'id': 2,
        'email': 'new@ema.il',
        'uploaded': 999,
        'downloaded': 998,
        })
    user = User.from_id(2)
    assert user.email == 'new@ema.il'
    assert user.uploaded == 999


def test_moderate_user_incomplete(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/2/moderate', data=json.dumps({
        'password': 'abcdefGHIfJK12#',
        }))
    check_json_response(response, {
        'id': 2,
        'email': 'paffu@puls.ar',
        'downloaded': 0,
        })
    user = User.from_id(2)
    assert user.check_password('abcdefGHIfJK12#')
    assert user.email == 'paffu@puls.ar'


def test_moderate_user_not_found(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/10/moderate', data=json.dumps({
        'email': 'new@ema.il',
        }))
    check_json_response(response, 'User 10 does not exist.')
    assert response.status_code == 404


def test_change_permissions(app, authed_client):
    add_permissions(app, 'change_password', 'list_user_classes', 'modify_user_classes')
    db.engine.execute("""INSERT INTO users_permissions (user_id, permission, granted)
                      VALUES (1, 'send_invites', 'f')""")
    db.engine.execute(
        """UPDATE user_classes
        SET permissions = '{"moderate_users", "moderate_users_advanced", "view_invites"}'""")

    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'permissions': {
            'moderate_users': False,
            'change_password': False,
            'view_invites': False,
            'send_invites': True,
        }})).get_json()

    assert set(response['response']['permissions']) == {
        'moderate_users_advanced', 'modify_user_classes', 'send_invites', 'list_user_classes'}

    u_perms = UserPermission.from_user(1)
    assert u_perms == {
        'list_user_classes': True,
        'modify_user_classes': True,
        'send_invites': True,
        'view_invites': False,
        'moderate_users': False,
        }


@pytest.mark.parametrize(
    'permissions, expected', [
        ({'send_invites': True, 'view_invites': False},
         'The following UserPermissions could not be added: send_invites.'),
        ({'change_password': False, 'send_invites': False},
         'The following UserPermissions could not be deleted: change_password.'),
        ({'legacy': False, 'view_invites': False},
         'legacy is not a valid permission.'),
    ])
def test_change_permissions_failure(app, authed_client, permissions, expected):
    add_permissions(app, 'moderate_users', 'moderate_users_advanced',
                    'send_invites', 'view_invites')
    db.engine.execute(
        """UPDATE user_classes SET permissions = '{"legacy"}'
        WHERE name = 'User'""")
    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'permissions': permissions}))
    check_json_response(response, expected)


def test_change_permissions_restricted(app, authed_client):
    """Basic but not advanced permissions privileges."""
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'permissions': {'moderate_users': False}}))
    check_json_response(
        response, 'Invalid data: moderate_users is not a valid permission (key "permissions")')


def test_change_forum_permissions(app, authed_client):
    add_permissions(app, 'moderate_users')
    add_permissions(app, 'forums_forums_permission_1', 'forums_threads_permission_1',
                    table='forums_permissions')
    db.engine.execute("""UPDATE user_classes
                      SET forum_permissions = '{"forums_forums_permission_2"}'""")

    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'forum_permissions': {
            'forums_forums_permission_2': False,
            'forums_threads_permission_1': False,
            'forums_threads_permission_2': True
        }})).get_json()

    print(response['response'])
    assert set(response['response']['forum_permissions']) == {
        'forums_forums_permission_1', 'forums_threads_permission_2'}

    f_perms = ForumPermission.from_user(1)
    assert f_perms == {
        'forums_forums_permission_2': False,
        'forums_forums_permission_1': True,
        'forums_threads_permission_2': True,
        }


def test_change_forum_permissions_failure(app, authed_client):
    add_permissions(app, 'moderate_users')
    add_permissions(app, 'forums_threads_permission_1', table='forums_permissions')
    db.engine.execute("""UPDATE user_classes
                      SET forum_permissions = '{"forums_forums_permission_2"}'""")

    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'forum_permissions': {
            'forums_forums_permission_2': True,
            'forums_threads_permission_1': False,
            'forums_threads_permission_4': False,
            'forums_threads_permission_2': True
        }}))

    check_json_response(
        response, 'The following ForumPermissions could not be added: forums_forums_permission_2. '
        'The following ForumPermissions could not be deleted: forums_threads_permission_4.')
    f_perms = ForumPermission.from_user(1)
    assert f_perms == {'forums_threads_permission_1': True}


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/users/1/moderate', 'PUT'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
