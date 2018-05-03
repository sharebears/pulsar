import json
import pytest
from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.users.models import User


def test_get_all_permissions(app, authed_client):
    add_permissions(app, 'list_permissions', 'manipulate_permissions')
    response = authed_client.get('/permissions', query_string={'all': 'true'})
    data = json.loads(response.get_data())['response']
    assert 'permissions' in data
    assert all(perm in data['permissions'] for perm in [
        'manipulate_permissions',
        'view_invites',
        'no_ip_tracking',
        ])
    assert all(len(perm) <= 32 for perm in data['permissions'])


def test_get_limited_permissions(app, authed_client):
    add_permissions(app, 'list_permissions')
    response = authed_client.get('/permissions')
    data = json.loads(response.get_data())['response']
    assert 'permissions' in data
    assert 'not_a_permission' not in data['permissions']


def test_get_permissions_other(app, authed_client):
    add_permissions(app, 'list_permissions', 'manipulate_permissions')
    response = authed_client.get('/permissions/user/2')
    check_json_response(response, {'permissions': []}, strict=True)


def test_choose_user_permission(app, authed_client):
    add_permissions(app, 'list_permissions')
    response = authed_client.get('/permissions/user/2')
    check_json_response(
        response, 'You do not have permission to access this resource.')
    assert response.status_code == 403


def test_change_permissions_success(app, authed_client):
    add_permissions(app, 'manipulate_permissions', 'send_invites')
    response = authed_client.put('/permissions/user/1', json={
        'permissions': {
            'send_invites': False,
            'view_invites': True,
        }})
    response = json.loads(response.get_data())
    assert 'response' in response and 'permissions' in response['response']
    assert all(perm in response['response']['permissions']
               for perm in ['manipulate_permissions', 'view_invites'])


@pytest.mark.parametrize(
    'permissions, expected', [
        ({'send_invites': True, 'view_invites': False},
         'lights already has the permission send_invites.'),
        ({'change_password': False, 'send_invites': False},
         'lights does not have the permission change_password.'),
    ])
def test_change_permissions_failure(app, authed_client, permissions, expected):
    add_permissions(app, 'manipulate_permissions', 'send_invites', 'view_invites')
    response = authed_client.put('/permissions/user/1', json={
        'permissions': permissions})
    check_json_response(response, expected)


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/permissions', 'GET'),
        ('/permissions/all', 'GET'),
        ('/permissions/user/1', 'PUT'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    assert response.status_code == 404


def test_user_class_permissions(app, authed_client):
    add_permissions(app, 'view_invites')
    db.engine.execute(
        """UPDATE user_classes SET permissions = '{"list_permissions"}'
        WHERE user_class = 'user'
        """)
    response = authed_client.get('/permissions')
    data = response.get_json()['response']
    assert all(perm in data['permissions'] for perm in [
        'list_permissions',
        'view_invites',
        ])


def test_user_class_permission_override(app, authed_client):
    db.engine.execute(
        """UPDATE user_classes SET permissions = '{"sample_a", "sample_b"}'""")
    db.engine.execute(
        """INSERT INTO users_permissions (user_id, permission, granted) VALUES
        (1, 'sample_c', 't'),
        (1, 'sample_d', 't'),
        (1, 'sample_b', 'f')
        """)

    user = User.from_id(1)
    assert all(len(
        [p for p in user.permissions if p == perm]) == 1
        for perm in user.permissions)
    assert set(user.permissions) == {'sample_a', 'sample_c', 'sample_d'}
