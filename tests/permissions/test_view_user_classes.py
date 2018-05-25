import json

import pytest

from conftest import check_json_response
from pulsar import db
from pulsar.models import SecondaryClass, UserClass


def test_view_user_class(app, authed_client):
    response = authed_client.get('/user_classes/1').get_json()
    assert 'response' in response
    response = response['response']
    assert response['name'] == 'User'
    assert set(response['permissions']) == {'modify_permissions', 'edit_settings'}


def test_view_user_class_secondary(app, authed_client):
    response = authed_client.get('/user_classes/2', query_string={
        'secondary': True}).get_json()
    assert 'response' in response
    response = response['response']
    assert response['name'] == 'user_v2'
    assert response['permissions'] == ['edit_settings']


def test_view_user_class_nonexistent(app, authed_client):
    response = authed_client.get('/user_classes/10').get_json()
    assert 'response' in response
    assert response['response'] == 'UserClass 10 does not exist.'


def test_view_multiple_user_classes(app, authed_client):
    response = authed_client.get('/user_classes').get_json()

    assert len(response['response']['user_classes']) == 2
    assert ({'id': 1,
             'name': 'User',
             'permissions': ['modify_permissions', 'edit_settings'],
             'forum_permissions': None} in response['response']['user_classes'])
    assert ({'id': 2,
             'name': 'user_v2',
             'permissions': ['modify_permissions', 'edit_settings'],
             'forum_permissions': None} in response['response']['user_classes'])

    assert len(response['response']['secondary_classes']) == 2
    assert ({'id': 1,
             'name': 'FLS',
             'permissions': ['send_invites'],
             'forum_permissions': None} in response['response']['secondary_classes'])
    assert ({'id': 2,
             'name': 'user_v2',
             'permissions': ['edit_settings'],
             'forum_permissions': None} in response['response']['secondary_classes'])


def test_create_user_class(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites']}))
    check_json_response(response, {
        'id': 3,
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites']})

    user_class = UserClass.from_pk(3)
    assert user_class.name == 'user_v3'
    assert user_class.permissions == ['edit_settings', 'send_invites']


def test_create_user_class_duplicate(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'user_v2', 'permissions': []})).get_json()
    assert response['response'] == 'Another UserClass already has the name user_v2.'


def test_create_user_class_secondary(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'User',
        'permissions': ['edit_settings', 'send_invites'],
        'secondary': True}))
    check_json_response(response, {
        'id': 3,
        'name': 'User',
        'permissions': ['edit_settings', 'send_invites']})

    user_class = SecondaryClass.from_pk(3)
    assert user_class.name == 'User'
    assert user_class.permissions == ['edit_settings', 'send_invites']

    assert not UserClass.from_pk(4)


def test_create_secondary_class_duplicate(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'user_v2', 'permissions': [], 'secondary': True})).get_json()
    assert response['response'] == 'Another SecondaryClass already has the name user_v2.'


def test_delete_user_class(app, authed_client):
    response = authed_client.delete('/user_classes/2').get_json()
    assert response['response'] == 'UserClass user_v2 has been deleted.'
    assert not UserClass.from_pk(2)
    assert not UserClass.from_name('user_v2')


def test_delete_user_class_nonexistent(app, authed_client):
    response = authed_client.delete('/user_classes/10').get_json()
    assert response['response'] == 'UserClass 10 does not exist.'


def test_delete_secondary_with_uc_name(app, authed_client):
    response = authed_client.delete('/user_classes/5', query_string={
        'secondary': True}).get_json()
    assert response['response'] == 'SecondaryClass 5 does not exist.'


def test_delete_user_class_with_user(app, authed_client):
    response = authed_client.delete('/user_classes/1').get_json()
    assert response['response'] == \
        'You cannot delete a UserClass while users are assigned to it.'
    assert UserClass.from_pk(1)


def test_delete_secondary_class_with_user(app, authed_client):
    response = authed_client.delete('/user_classes/1', query_string={
        'secondary': True}).get_json()
    assert response['response'] == \
        'You cannot delete a SecondaryClass while users are assigned to it.'
    assert SecondaryClass.from_pk(1)


def test_modify_user_class(app, authed_client):
    response = authed_client.put('/user_classes/1', data=json.dumps({
        'permissions': {
            'edit_settings': False,
            'send_invites': True,
        }}))
    check_json_response(response, {
        'name': 'User',
        'permissions': ['modify_permissions', 'send_invites']})
    user_class = UserClass.from_pk(1)
    assert set(user_class.permissions) == {'modify_permissions', 'send_invites'}


def test_modify_secondary_user_class(app, authed_client):
    authed_client.put('/user_classes/2', data=json.dumps({
        'permissions': {'edit_settings': False},
        'secondary': True,
        }))

    secondary_class = SecondaryClass.from_pk(2)
    assert not secondary_class.permissions

    user_class = UserClass.from_pk(2)
    assert 'edit_settings' in user_class.permissions


@pytest.mark.parametrize(
    'permissions, error', [
        ({'edit_settings': True},
         'UserClass User already has the permission edit_settings.'),
        ({'send_invites': False},
         'UserClass User does not have the permission send_invites.'),
    ])
def test_modify_user_class_failure(app, authed_client, permissions, error):
    response = authed_client.put('/user_classes/1', data=json.dumps({
        'permissions': permissions})).get_json()
    assert response['response'] == error


def test_modify_user_class_nonexistent(app, authed_client):
    response = authed_client.put('/user_classes/3', data=json.dumps({
        'permissions': {'send_invites': True}})).get_json()
    assert response['response'] == 'UserClass 3 does not exist.'


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/user_classes/1', 'GET'),
        ('/user_classes', 'GET'),
        ('/user_classes', 'POST'),
        ('/user_classes/5', 'DELETE'),
        ('/user_classes/6', 'PUT'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    db.engine.execute("DELETE FROM users_permissions")
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
