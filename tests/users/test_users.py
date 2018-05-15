import json
import pytest
from sqlalchemy.exc import IntegrityError
from conftest import check_json_response, add_permissions
from pulsar import db, cache, APIException
from pulsar.models import User


def test_user_creation(app, client):
    user = User.new(
        username='bright',
        password='13579',
        email='bright@puls.ar')
    assert isinstance(user.id, int) and user.id > 1


def test_user_creation_dupe_username(app, client):
    with pytest.raises(APIException) as e:
        User.new(
            username='ligHts',
            password='13579',
            email='bright@puls.ar')
    assert str(e.value.message) == 'The username ligHts is already in use.'


def test_user_creation_dupe_username_database(app, client):
    with pytest.raises(IntegrityError):
        db.session.execute(
            """INSERT INTO users (username, passhash, email) VALUES
            ('LiGhTs', '13579', 'bright@puls.ar')""")


def test_user_obj(app, client):
    user_id = User.from_id(1)
    user_name = User.from_username('lights')
    assert repr(user_id) == f'<User 1>'
    assert user_id == user_name


def test_user_passwords(app, client):
    user = User.from_id(1)
    user.set_password('secure password')
    assert user.check_password('secure password')


def test_user_has_permission(app, client):
    add_permissions(app, 'sample_permission')
    user = User.from_id(1)
    assert user.has_permission('sample_permission')
    assert not user.has_permission('nonexistent_permission')


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
        'user_class': {
            'id': 1,
            'name': 'User',
        }
        })
    assert response.status_code == 200
    data = response.get_json()
    assert 'user_class' in data['response']
    assert data['response']['user_class']['id'] == 1
    assert data['response']['user_class']['name'] == 'User'
    assert 'api_keys' not in data['response']
    assert 'email' not in data['response']


def test_get_user_detailed(app, authed_client):
    add_permissions(app, 'view_users', 'moderate_users')
    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1,
        'username': 'lights',
        'user_class': {
            'id': 1,
            'name': 'User',
        },
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
