import json
import pytest
from voluptuous import Invalid
from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.users.models import User
from pulsar.permissions.models import UserClass, SecondaryUserClass


@pytest.fixture(autouse=True)
def populate_db(app, client):
    add_permissions(app, 'list_user_classes', 'modify_user_classes')
    db.engine.execute("""UPDATE user_classes
                      SET permissions = '{"list_permissions", "view_invites"}'
                      WHERE name = 'User'""")
    db.engine.execute("""UPDATE secondary_classes
                      SET permissions = '{"send_invites"}'
                      WHERE name = 'FLS'""")
    db.engine.execute("""INSERT INTO user_classes (name, permissions) VALUES
                      ('user_v2', '{"manipulate_permissions", "list_permissions"}')""")
    db.engine.execute("""INSERT INTO secondary_classes (name, permissions) VALUES
                      ('user_v2', '{"list_permissions"}')""")


def test_view_user_class(app, authed_client):
    response = authed_client.get('/user_classes/user').get_json()
    assert 'response' in response
    response = response['response']
    assert response['name'] == 'User'
    assert set(response['permissions']) == {'list_permissions', 'view_invites'}


def test_view_user_class_secondary(app, authed_client):
    response = authed_client.get('/user_classes/user_v2', query_string={
        'secondary': True}).get_json()
    assert 'response' in response
    response = response['response']
    assert response['name'] == 'user_v2'
    assert response['permissions'] == ['list_permissions']


def test_view_user_class_nonexistent(app, authed_client):
    response = authed_client.get('/user_classes/non_existent').get_json()
    assert 'response' in response
    assert response['response'] == 'User class non_existent does not exist.'


def test_view_multiple_user_classes(app, authed_client):
    response = authed_client.get('/user_classes').get_json()

    assert len(response['response']['user_classes']) == 2
    assert ({'name': 'User', 'permissions': ['list_permissions', 'view_invites']}
            in response['response']['user_classes'])
    assert ({'name': 'user_v2', 'permissions': ['manipulate_permissions', 'list_permissions']}
            in response['response']['user_classes'])

    assert len(response['response']['secondary_classes']) == 2
    assert ({'name': 'FLS', 'permissions': ['send_invites']}
            in response['response']['secondary_classes'])
    assert ({'name': 'user_v2', 'permissions': ['list_permissions']}
            in response['response']['secondary_classes'])


def test_create_user_class_schema(app, authed_client):
    from pulsar.permissions.user_classes import create_user_class_schema
    data = {
        'name': 'user_v3',
        'permissions': ['list_permissions', 'send_invites'],
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
        'permissions': ['list_permissions', 'send_invites']}))
    check_json_response(response, {
        'name': 'user_v3',
        'permissions': ['list_permissions', 'send_invites']})

    user_class = UserClass.from_name('user_v3')
    assert user_class.name == 'user_v3'
    assert user_class.permissions == ['list_permissions', 'send_invites']


def test_create_user_class_duplicate(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'user_v2', 'permissions': []})).get_json()
    assert response['response'] == 'Another user class is already named user_v2.'


def test_create_user_class_secondary(app, authed_client):
    response = authed_client.post('/user_classes', data=json.dumps({
        'name': 'User',
        'permissions': ['list_permissions', 'send_invites'],
        'secondary': True}))
    check_json_response(response, {
        'name': 'User',
        'permissions': ['list_permissions', 'send_invites']})

    user_class = SecondaryUserClass.from_name('User')
    assert user_class.name == 'User'
    assert user_class.permissions == ['list_permissions', 'send_invites']

    assert not UserClass.from_name('user_v3')


def test_delete_user_class(app, authed_client):
    response = authed_client.delete('/user_classes/user_v2').get_json()
    assert response['response'] == 'User class user_v2 has been deleted.'
    assert not UserClass.from_name('user_v2')


def test_delete_user_class_nonexistent(app, authed_client):
    response = authed_client.delete('/user_classes/user_v4').get_json()
    assert response['response'] == 'User class user_v4 does not exist.'


def test_delete_secondary_with_uc_name(app, authed_client):
    response = authed_client.delete('/user_classes/User', query_string={
        'secondary': True}).get_json()
    assert response['response'] == 'Secondary class User does not exist.'


def test_delete_user_class_with_user(app, authed_client):
    user = User.from_id(2)
    user.user_class = 'user_v2'
    db.session.commit()

    response = authed_client.delete('/user_classes/user_v2').get_json()
    assert response['response'] == \
        'You cannot delete a user class while users are assigned to it.'
    assert UserClass.from_name('user_v2')


def test_modify_user_class_schema(app, authed_client):
    from pulsar.permissions.user_classes import modify_user_class_schema
    data = {
        'permissions': {
            'manipulate_permissions': False,
            'list_permissions': True
            },
        'secondary': True,
        }
    data == modify_user_class_schema(data)


def test_modify_user_class(app, authed_client):
    response = authed_client.put('/user_classes/user', data=json.dumps({
        'permissions': {
            'list_permissions': False,
            'send_invites': True,
        }}))
    check_json_response(response, {
        'name': 'User',
        'permissions': ['view_invites', 'send_invites']})
    user_class = UserClass.from_name('user')
    assert set(user_class.permissions) == {'view_invites', 'send_invites'}


def test_modify_secondary_user_class(app, authed_client):
    authed_client.put('/user_classes/user_v2', data=json.dumps({
        'permissions': {'list_permissions': False},
        'secondary': True,
        }))

    secondary_class = SecondaryUserClass.from_name('user_v2')
    assert not secondary_class.permissions

    user_class = UserClass.from_name('user_v2')
    assert 'list_permissions' in user_class.permissions


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


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/user_classes/user', 'GET'),
        ('/user_classes', 'GET'),
        ('/user_classes', 'POST'),
        ('/user_classes/usar', 'DELETE'),
        ('/user_classes/usir', 'PUT'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    db.engine.execute("DELETE FROM users_permissions")
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
