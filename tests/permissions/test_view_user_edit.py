import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.models import UserPermission


def test_get_all_permissions(app, authed_client):
    add_permissions(app, 'modify_permissions')
    response = authed_client.get('/permissions')
    data = json.loads(response.get_data())['response']
    assert 'permissions' in data
    assert all(perm in data['permissions'] for perm in [
        'modify_permissions',
        'view_invites',
        'no_ip_tracking',
        ])
    assert all(len(perm) <= 32 for perm in data['permissions'])


def test_change_permissions(app, authed_client):
    add_permissions(app, 'modify_permissions', 'change_password')
    db.engine.execute("INSERT INTO users_permissions VALUES (1, 'send_invites', 'f')")
    db.engine.execute("""UPDATE user_classes
                       SET permissions = '{"modify_permissions", "view_invites"}'""")

    response = authed_client.put('/permissions/user/1', data=json.dumps({
        'permissions': {
            'modify_permissions': False,
            'change_password': False,
            'view_invites': False,
            'send_invites': True,
        }})).get_json()

    assert set(response['response']['permissions']) == {
        'modify_user_classes', 'send_invites', 'list_user_classes'}

    u_perms = UserPermission.from_user(1)
    assert u_perms == {
        'list_user_classes': True,
        'modify_user_classes': True,
        'send_invites': True,
        'view_invites': False,
        'modify_permissions': False,
        }


@pytest.mark.parametrize(
    'permissions, expected', [
        ({'send_invites': True, 'view_invites': False},
         'The following permissions could not be added: send_invites.'),
        ({'change_password': False, 'send_invites': False},
         'The following permissions could not be deleted: change_password.'),
        ({'legacy': False, 'view_invites': False},
         'legacy is not a valid permission.'),
    ])
def test_change_permissions_failure(app, authed_client, permissions, expected):
    add_permissions(app, 'modify_permissions', 'send_invites', 'view_invites')
    db.engine.execute(
        """UPDATE user_classes SET permissions = '{"legacy"}'
        WHERE name = 'User'""")
    response = authed_client.put('/permissions/user/1', data=json.dumps({
        'permissions': permissions}))
    check_json_response(response, expected)


def test_user_class_permissions(app, authed_client):
    add_permissions(app, 'view_invites')
    db.engine.execute(
        """UPDATE user_classes SET permissions = '{"modify_permissions"}'
        WHERE name = 'User'
        """)
    response = authed_client.get('/permissions')
    data = response.get_json()['response']
    assert all(perm in data['permissions'] for perm in [
        'modify_permissions',
        'view_invites',
        'modify_user_classes',
        ])


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/permissions', 'GET'),
        ('/permissions/user/1', 'PUT'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    db.engine.execute("DELETE FROM users_permissions")
    db.engine.execute("UPDATE user_classes SET permissions = '{}'")
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403


def test_get_all_permissions_permission(authed_client):
    db.engine.execute("DELETE FROM users_permissions")
    db.engine.execute("UPDATE user_classes SET permissions = '{}'")
    response = authed_client.get('/permissions', query_string={'all': 'true'})
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
