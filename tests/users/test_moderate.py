import json
import pytest
from voluptuous import MultipleInvalid
from conftest import check_json_response, add_permissions
from pulsar import db
from pulsar.models import User
from pulsar.users.moderate import moderate_user_schema


def test_int_overflow(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'invites': 99999999999999999999999999,
        }))
    check_json_response(response, 'Invalid data: value must be at most 2147483648 (key "invites")')


def test_locked_acc_perms_blocked(app, client):
    db.engine.execute("UPDATE users SET locked = 't' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_id'] = 'bcdefghijk'

    response = client.get('/users/1')
    check_json_response(response, 'Your account has been locked.')


def test_locked_acc_perms_can_access(app, client):
    db.engine.execute("UPDATE users SET locked = 't' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_id'] = 'bcdefghijk'
    app.config['LOCKED_ACCOUNT_PERMISSIONS'] = 'view_users'

    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.get_json()['response']['id'] == 1


@pytest.mark.parametrize(
    'schema', [
        {'email': 'new@ema.il'},
        {'email': 'new@ema.il', 'password': 'abcdefGHIfJK12#'},
        {'downloaded': 123123123, 'invites': 104392},
    ])
def test_moderate_user_schema(schema):
    assert schema == moderate_user_schema(schema)


@pytest.mark.parametrize(
    'schema, error', [
        ({'email': 'new@ema.il', 'password': '1231233281FF'},
         "Password must be 12 or more characters and contain at least 1 letter, "
         "1 number, and 1 special character, for dictionary value @ data['password']"),
        ({'uploaded': 12313, 'extra': 0},
         "extra keys not allowed @ data['extra']"),
    ])
def test_moderate_user_schema_failure(schema, error):
    with pytest.raises(MultipleInvalid) as e:
        moderate_user_schema(schema)
    assert str(e.value) == error


def test_moderate_user(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/2/moderate', data=json.dumps({
        'email': 'new@ema.il',
        'uploaded': 999,
        'downloaded': 998,
        'invites': 100,
        }))
    check_json_response(response, {
        'id': 2,
        'email': 'new@ema.il',
        'uploaded': 999,
        'downloaded': 998,
        })
    user = User.from_id(2)
    assert user.email == 'new@ema.il'
    assert user.uploaded == 999


def test_moderate_user_incomplete(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/2/moderate', data=json.dumps({
        'password': 'abcdefGHIfJK12#',
        }))
    check_json_response(response, {
        'id': 2,
        'email': 'paffu@puls.ar',
        'downloaded': 0,
        })
    user = User.from_id(2)
    assert user.check_password('abcdefGHIfJK12#')
    assert user.email == 'paffu@puls.ar'


def test_moderate_user_not_found(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/10/moderate', data=json.dumps({
        'email': 'new@ema.il',
        }))
    check_json_response(response, 'User 10 does not exist.')
    assert response.status_code == 404
