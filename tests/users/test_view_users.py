import json

import pytest

from conftest import CODE_1, CODE_2, CODE_4, add_permissions, check_json_response
from pulsar import cache


def test_get_user_self_and_caches(app, authed_client):
    add_permissions(app, 'view_users')
    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1,
        'username': 'user_one',
        'secondary_classes': ['FLS'],
        })
    assert response.status_code == 200
    user_data = cache.get('users_1')
    assert user_data['user_class_id'] == 1
    assert user_data['id'] == 1
    assert user_data['username'] == 'user_one'


def test_get_user(app, authed_client):
    add_permissions(app, 'view_users')
    response = authed_client.get('/users/2')
    check_json_response(response, {
        'id': 2,
        'username': 'user_two',
        'user_class': 'User',
        })
    assert response.status_code == 200
    data = response.get_json()
    assert 'user_class' in data['response']
    assert not data['response']['api_keys']
    assert not data['response']['email']


def test_get_user_detailed(app, authed_client):
    add_permissions(app, 'view_users', 'moderate_users')
    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1,
        'username': 'user_one',
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'downloaded': 0,
        'email': 'user_one@puls.ar',
        })
    assert response.status_code == 200
    data = response.get_json()
    assert 'api_keys' in data['response']
    assert len(data['response']['api_keys']) == 2
    assert any(ak['hash'] == 'abcdefghij' for ak in data['response']['api_keys'])


def test_user_does_not_exist(app, authed_client):
    add_permissions(app, 'view_users')
    response = authed_client.get('/users/4')
    check_json_response(response, 'User 4 does not exist.', strict=True)
    assert response.status_code == 404


@pytest.mark.parametrize(
    'existing_password, new_password, message', [
        ('12345', 'aB1%ckeofa12342', 'Settings updated.'),
        ('54321', 'aB1%ckeofa12342', 'Invalid existing password.'),
    ])
def test_edit_settings(app, authed_client, existing_password, new_password, message):
    add_permissions(app, 'edit_settings', 'change_password')
    response = authed_client.put('/users/settings', data=json.dumps({
        'existing_password': existing_password,
        'new_password': new_password,
        }))
    check_json_response(response, message, strict=True)


def test_edit_settings_pw_fail(app, authed_client):
    add_permissions(app, 'edit_settings')
    response = authed_client.put('/users/settings', data=json.dumps({
        'existing_password': '12345',
        'new_password': 'aB1%ckeofa12342',
        }))
    check_json_response(
        response, 'You do not have permission to change this password.')


def test_edit_settings_others(app, authed_client):
    add_permissions(app, 'edit_settings', 'change_password', 'moderate_users')
    response = authed_client.put('/users/2/settings', data=json.dumps({
        }))
    check_json_response(response, 'Settings updated.', strict=True)


@pytest.mark.parametrize(
    'code, status_code, expected', [
        (CODE_1, 200, {'username': 'bright'}),
        (None, 400, 'An invite code is required for registration.'),
        (CODE_2, 400, f'{CODE_2} is not a valid invite code.'),
        (CODE_4, 400, f'{CODE_4} is not a valid invite code.'),
    ])
def test_register_with_code(app, client, code, status_code, expected):
    app.config['REQUIRE_INVITE_CODE'] = True
    endpoint = f'/users' if code else '/users'
    response = client.post(endpoint, data=json.dumps({
        'username': 'bright',
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar',
        'code': code,
        }))
    check_json_response(response, expected, strict=True)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    'username, status_code, expected', [
        ('bright', 200, {'username': 'bright'}),
        ('user_one', 400, 'Invalid data: another user already has the username '
                          'user_one (key "username")'),
    ])
def test_registration(app, client, username, status_code, expected):
    app.config['REQUIRE_INVITE_CODE'] = False
    response = client.post('/users', data=json.dumps({
        'username': username,
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar'}))
    check_json_response(response, expected, strict=True)
    assert response.status_code == status_code


def test_registration_no_code(app, client):
    app.config['REQUIRE_INVITE_CODE'] = True
    response = client.post('/users', data=json.dumps({
        'username': 'abiejfaiwof',
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar'}))
    check_json_response(response, 'An invite code is required for registration.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/users/1', 'GET'),
        ('/users/settings', 'PUT'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
