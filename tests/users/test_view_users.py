import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar import cache


def test_get_user_self_and_caches(app, authed_client):
    add_permissions(app, 'view_users')
    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1,
        'username': 'lights',
        'secondary_classes': ['FLS'],
        })
    assert response.status_code == 200
    user_data = cache.get('users_1')
    assert user_data['user_class_id'] == 1
    assert user_data['id'] == 1
    assert user_data['username'] == 'lights'


def test_get_user(app, authed_client):
    add_permissions(app, 'view_users')
    response = authed_client.get('/users/2')
    check_json_response(response, {
        'id': 2,
        'username': 'paffu',
        'user_class': 'User',
        })
    assert response.status_code == 200
    data = response.get_json()
    assert 'user_class' in data['response']
    assert 'api_keys' not in data['response']
    assert 'email' not in data['response']


def test_get_user_detailed(app, authed_client):
    add_permissions(app, 'view_users', 'moderate_users')
    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1,
        'username': 'lights',
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'downloaded': 0,
        'email': 'lights@puls.ar',
        })
    assert response.status_code == 200
    data = response.get_json()
    assert 'api_keys' in data['response']
    assert len(data['response']['api_keys']) == 1
    assert data['response']['api_keys'][0]['id'] == 'abcdefghij'


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
    'endpoint, method', [
        ('/users/1', 'GET'),
        ('/users/settings', 'PUT'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
