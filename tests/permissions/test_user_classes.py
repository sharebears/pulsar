import json
import pytest
from voluptuous import Invalid
from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.users.models import User
from pulsar.permissions.models import UserClass


@pytest.fixture(autouse=True)
def populate_db(app, client):
    add_permissions(app, 'list_user_classes', 'modify_user_classes')
    db.engine.execute("""UPDATE user_classes
                      SET permissions = '{"list_permissions", "view_invites"}'
                      WHERE user_class = 'User'""")
    db.engine.execute("""INSERT INTO user_classes (user_class, permissions) VALUES
                      ('user_v2', '{"manipulate_permissions", "list_permissions"}')""")


def test_view_user_class(app, authed_client):
    response = authed_client.get('/user_classes/user').get_json()
    assert 'response' in response
    response = response['response']
    assert response['user_class'] == 'User'
    assert set(response['permissions']) == {'list_permissions', 'view_invites'}


def test_view_user_class_nonexistent(app, authed_client):
    response = authed_client.get('/user_classes/non_existent').get_json()
    assert 'response' in response
    assert response['response'] == 'User class non_existent does not exist.'


def test_view_multiple_user_classes(app, authed_client):
    response = authed_client.get('/user_classes').get_json()
    assert len(response['response']) == 2
    assert {'user_class': 'User', 'permissions': [
        'list_permissions', 'view_invites']} in response['response']
    assert {'user_class': 'user_v2', 'permissions': [
        'manipulate_permissions', 'list_permissions']} in response['response']


def test_create_user_class_schema(app, authed_client):
    from pulsar.permissions.views.user_classes import create_user_class_schema
    data = {
        'user_class': 'user_v3',
        'permissions': ['list_permissions', 'send_invites'],
        }
    assert data == create_user_class_schema(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'user_class': 'user_v2', 'permissions': ['list_permissions', 'send_invites']},
         "Invalid data: user_v2 is taken by another user class, for dictionary value @ "
         "data['user_class']"),
        ({'user_class': 'user_v3', 'permissions': ['non_existent_permission']},
         "The following permissions are invalid: non_existent_permission, for dictionary "
         "value @ data['permissions']"),
    ])
def test_create_user_class_schema_failure(app, authed_client, data, error):
    from pulsar.permissions.views.user_classes import create_user_class_schema
    with pytest.raises(Invalid) as e:
        create_user_class_schema(data)
    assert str(e.value) == error


def test_create_user_class(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'user_class': 'user_v3',
        'permissions': ['list_permissions', 'send_invites']}))
    check_json_response(response, {
        'user_class': 'user_v3',
        'permissions': ['list_permissions', 'send_invites']})

    user_class = UserClass.from_name('user_v3')
    assert user_class.user_class == 'user_v3'
    assert user_class.permissions == ['list_permissions', 'send_invites']


def test_delete_user_class(app, authed_client):
    response = authed_client.delete('/user_classes/user_v2').get_json()
    assert response['response'] == 'User class user_v2 has been deleted.'
    assert not UserClass.from_name('user_v2')


def test_delete_user_class_nonexistent(app, authed_client):
    response = authed_client.delete('/user_classes/user_v4').get_json()
    assert response['response'] == 'User class user_v4 does not exist.'


def test_delete_user_class_with_user(app, authed_client):
    user = User.from_id(2)
    user.user_class = 'user_v2'
    db.session.commit()

    response = authed_client.delete('/user_classes/user_v2').get_json()
    assert response['response'] == \
        'You cannot delete a user class while users are assigned to it.'
    assert UserClass.from_name('user_v2')


def test_modify_user_class_schema(app, authed_client):
    from pulsar.permissions.views.user_classes import modify_user_class_schema
    data = {'permissions': {'manipulate_permissions': False, 'list_permissions': True}}
    assert data == modify_user_class_schema(data)


def test_modify_user_class(app, authed_client):
    response = authed_client.put('/user_classes/user', data=json.dumps({
        'permissions': {
            'list_permissions': False,
            'send_invites': True,
        }}))
    check_json_response(response, {
        'user_class': 'User',
        'permissions': ['view_invites', 'send_invites']})


@pytest.mark.parametrize(
    'permissions, error', [
        ({'list_permissions': True},
         'User class User already has the permission list_permissions.'),
        ({'send_invites': False},
         'User class User does not have the permission send_invites.'),
    ])
def test_modify_user_class_failure(app, authed_client, permissions, error):
    response = authed_client.put('/user_classes/user', data=json.dumps({
        'permissions': permissions})).get_json()
    assert response['response'] == error


def test_modify_user_class_nonexistent(app, authed_client):
    response = authed_client.put('/user_classes/kukuku', data=json.dumps({
        'permissions': {'send_invites': True}})).get_json()
    assert response['response'] == 'User class kukuku does not exist.'
