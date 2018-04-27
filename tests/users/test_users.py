import pytest
from conftest import check_json_response, add_permissions
from pulsar import db
from pulsar.users.models import User


def test_user_creation(app):
    with app.app_context():
        user = User('bright', '13579', 'bright@puls.ar')
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


def test_get_user(authed_client):
    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1, 'username': 'lights'})
    assert response.status_code == 200


def test_get_user_unauthed(client):
    response = client.get('/users/1')
    assert response.status_code == 404
    check_json_response(response, 'Resource does not exist.')


def test_user_does_not_exist(authed_client):
    response = authed_client.get('/users/4')
    check_json_response(response, 'User does not exist.', strict=True)
    assert response.status_code == 404


@pytest.mark.parametrize(
    'existing_password, new_password, message', [
        ('12345', 'aB1%ckeofa12342', 'Password changed.'),
        ('54321', 'aB1%ckeofa12342', 'Invalid existing password.'),
    ])
def test_change_password(app, authed_client, existing_password, new_password, message):
    add_permissions(app, 'change_password')
    response = authed_client.post('/users/change_password', json={
        'existing_password': existing_password,
        'new_password': new_password,
        })
    check_json_response(response, message, strict=True)


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/users/change_password', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'Resource does not exist.')
    assert response.status_code == 404
