import json

import pytest
from sqlalchemy.exc import IntegrityError
from voluptuous import Invalid

from conftest import check_json_response
from pulsar import APIException, cache, db
from pulsar.models import SecondaryClass, UserClass


@pytest.mark.parametrize(
    'class_, name', [
        (UserClass, 'UsEr'), (SecondaryClass, 'Fls')
    ])
def test_create_dupe_user_classes(app, client, class_, name):
    with pytest.raises(APIException):
        class_.new(
            name=name,
            permissions=None)


@pytest.mark.parametrize(
    'class_, name', [
        ('user_classes', 'USeR'), ('secondary_classes', 'fLS')
    ])
def test_create_dupe_user_classes_database(app, client, class_, name):
    with pytest.raises(IntegrityError):
        db.session.execute(f"INSERT INTO {class_} (name) VALUES ('{name}')")


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
    assert response['response'] == 'User class 10 does not exist.'


def test_view_multiple_user_classes(app, authed_client):
    response = authed_client.get('/user_classes').get_json()

    assert len(response['response']['user_classes']) == 2
    assert ({'id': 1, 'name': 'User', 'permissions': ['modify_permissions', 'edit_settings']}
            in response['response']['user_classes'])
    assert ({'id': 2, 'name': 'user_v2', 'permissions': ['modify_permissions', 'edit_settings']}
            in response['response']['user_classes'])

    assert len(response['response']['secondary_classes']) == 2
    assert ({'id': 1, 'name': 'FLS', 'permissions': ['send_invites']}
            in response['response']['secondary_classes'])
    assert ({'id': 2, 'name': 'user_v2', 'permissions': ['edit_settings']}
            in response['response']['secondary_classes'])


def test_create_user_class_schema(app, authed_client):
    from pulsar.permissions.user_classes import create_user_class_schema
    data = {
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites'],
        }
    response_data = create_user_class_schema(data)
    data['secondary'] = False
    assert response_data == data


@pytest.mark.parametrize(
    'data, error', [
        ({'name': 'user_v3', 'secondary': True, 'permissions': ['non_existent_permission']},
         "The following permissions are invalid: non_existent_permission, for dictionary "
         "value @ data['permissions']"),
    ])
def test_create_user_class_schema_failure(app, authed_client, data, error):
    from pulsar.permissions.user_classes import create_user_class_schema
    with pytest.raises(Invalid) as e:
        create_user_class_schema(data)
    assert str(e.value) == error


def test_create_user_class(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites']}))
    check_json_response(response, {
        'id': 3,
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites']})

    user_class = UserClass.from_id(3)
    assert user_class.name == 'user_v3'
    assert user_class.permissions == ['edit_settings', 'send_invites']


def test_create_user_class_duplicate(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'user_v2', 'permissions': []})).get_json()
    assert response['response'] == 'Another user class already has the name user_v2.'


def test_create_user_class_secondary(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'User',
        'permissions': ['edit_settings', 'send_invites'],
        'secondary': True}))
    check_json_response(response, {
        'id': 3,
        'name': 'User',
        'permissions': ['edit_settings', 'send_invites']})

    user_class = SecondaryClass.from_id(3)
    assert user_class.name == 'User'
    assert user_class.permissions == ['edit_settings', 'send_invites']

    assert not UserClass.from_id(4)


def test_delete_user_class(app, authed_client):
    response = authed_client.delete('/user_classes/2').get_json()
    assert response['response'] == 'User class user_v2 has been deleted.'
    assert not UserClass.from_id(2)
    assert not UserClass.from_name('user_v2')


def test_delete_user_class_nonexistent(app, authed_client):
    response = authed_client.delete('/user_classes/10').get_json()
    assert response['response'] == 'User class 10 does not exist.'


def test_delete_secondary_with_uc_name(app, authed_client):
    response = authed_client.delete('/user_classes/5', query_string={
        'secondary': True}).get_json()
    assert response['response'] == 'Secondary class 5 does not exist.'


def test_delete_user_class_with_user(app, authed_client):
    response = authed_client.delete('/user_classes/1').get_json()
    assert response['response'] == \
        'You cannot delete a user class while users are assigned to it.'
    assert UserClass.from_id(1)


def test_delete_secondary_class_with_user(app, authed_client):
    response = authed_client.delete('/user_classes/1', query_string={
        'secondary': True}).get_json()
    assert response['response'] == \
        'You cannot delete a secondary class while users are assigned to it.'
    assert SecondaryClass.from_id(1)


def test_modify_user_class_schema(app, authed_client):
    from pulsar.permissions.user_classes import modify_user_class_schema
    data = {
        'permissions': {
            'modify_permissions': False,
            'edit_settings': True
            },
        'secondary': True,
        }
    data == modify_user_class_schema(data)


def test_modify_user_class(app, authed_client):
    response = authed_client.put('/user_classes/1', data=json.dumps({
        'permissions': {
            'edit_settings': False,
            'send_invites': True,
        }}))
    check_json_response(response, {
        'name': 'User',
        'permissions': ['modify_permissions', 'send_invites']})
    user_class = UserClass.from_id(1)
    assert set(user_class.permissions) == {'modify_permissions', 'send_invites'}


def test_modify_secondary_user_class(app, authed_client):
    authed_client.put('/user_classes/2', data=json.dumps({
        'permissions': {'edit_settings': False},
        'secondary': True,
        }))

    secondary_class = SecondaryClass.from_id(2)
    assert not secondary_class.permissions

    user_class = UserClass.from_id(2)
    assert 'edit_settings' in user_class.permissions


@pytest.mark.parametrize(
    'permissions, error', [
        ({'edit_settings': True},
         'User class User already has the permission edit_settings.'),
        ({'send_invites': False},
         'User class User does not have the permission send_invites.'),
    ])
def test_modify_user_class_failure(app, authed_client, permissions, error):
    response = authed_client.put('/user_classes/1', data=json.dumps({
        'permissions': permissions})).get_json()
    assert response['response'] == error


def test_modify_user_class_nonexistent(app, authed_client):
    response = authed_client.put('/user_classes/3', data=json.dumps({
        'permissions': {'send_invites': True}})).get_json()
    assert response['response'] == 'User class 3 does not exist.'


@pytest.mark.parametrize(
    'class_, class_id, permission', [
        (UserClass, 1, 'edit_settings'),
        (SecondaryClass, 1, 'send_invites'),
    ])
def test_user_class_cache(app, client, class_, class_id, permission):
    user_class = class_.from_id(class_id)
    cache_key = cache.cache_model(user_class, timeout=60)
    user_class = class_.from_id(class_id)
    assert user_class.id == class_id
    assert permission in user_class.permissions
    assert cache.ttl(cache_key) < 61


@pytest.mark.parametrize(
    'class_', [UserClass, SecondaryClass])
def test_user_class_cache_get_all(app, client, class_):
    cache.set(class_.__cache_key_all__, [2], timeout=60)
    all_user_classes = class_.get_all()
    assert len(all_user_classes) == 1
    assert 'edit_settings' in all_user_classes[0].permissions


def test_user_secondary_classes_models(app, client):
    cache.set(SecondaryClass.__cache_key_of_user__.format(id=1), [2], timeout=60)
    secondary_classes = SecondaryClass.from_user(1)
    assert len(secondary_classes) == 1
    assert secondary_classes[0].name == 'user_v2'


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
