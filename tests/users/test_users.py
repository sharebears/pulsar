import json
import pytest
from conftest import check_json_response, add_permissions, HASHED_CODE_1
from pulsar import db, cache
from pulsar.users.models import User


@pytest.fixture(autouse=True)
def populate_db(app, client):
    yield
    db.engine.execute("DELETE FROM api_keys")


def test_user_creation(app):
    with app.app_context():
        user = User.register(
            username='bright',
            password='13579',
            email='bright@puls.ar')
        db.session.add(user)
        db.session.commit()
        assert isinstance(user.id, int) and user.id > 1


def test_user_obj(app):
    with app.app_context():
        user_id = User.from_id(1)
        user_name = User.from_username('lights')
        assert repr(user_id) == f'<User 1>'
        assert user_id == user_name


def test_user_passwords(app):
    with app.app_context():
        user = User.from_id(1)
        user.set_password('secure password')
        assert user.check_password('secure password')


def test_user_has_permission(app):
    with app.app_context():
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
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        })
    assert response.status_code == 200
    user_data = cache.get('users_1')
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
    assert 'api_keys' not in data['response']
    assert 'email' not in data['response']


def test_get_user_detailed(app, authed_client):
    add_permissions(app, 'view_users', 'moderate_users')
    db.engine.execute(
        f"""INSERT INTO api_keys (user_id, hash, keyhashsalt, active, permissions) VALUES
        (1, 'abcdefghij', '{HASHED_CODE_1}', 't',
         '{{"sample_permission", "sample_2_permission", "sample_3_permission"}}')""")
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
    assert data['response']['api_keys'][0]['hash'] == 'abcdefghij'


def test_user_does_not_exist(app, authed_client):
    add_permissions(app, 'view_users')
    response = authed_client.get('/users/4')
    check_json_response(response, 'User does not exist.', strict=True)
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
        'existing_password': 'abcdefg',
        'new_password': 'aB1%ckeofa12342',
        }))
    check_json_response(response, 'Settings updated.', strict=True)
    user = User.from_id(2)
    assert user.check_password('aB1%ckeofa12342')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/users/1', 'GET'),
        ('/users/settings', 'PUT'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
