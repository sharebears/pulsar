import json
import pytest
from voluptuous import Invalid, MultipleInvalid
from conftest import CODE_2, check_json_response, add_permissions
from pulsar import db
from pulsar.models import User
from pulsar.users.validators import ration_bytes
from pulsar.users.moderate import moderate_user_schema


def test_locked_acc_perms_blocked(app, client):
    db.engine.execute(
        f"""INSERT INTO sessions (hash, user_id, csrf_token) VALUES
        ('bcdefghijk', 2, '{CODE_2}')""")
    db.engine.execute("UPDATE users SET locked = 't' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_hash'] = 'bcdefghijk'

    response = client.get('/users/1')
    check_json_response(response, 'Your account has been locked.')


def test_locked_acc_perms_can_access(app, client):
    db.engine.execute(
        f"""INSERT INTO sessions (hash, user_id, csrf_token) VALUES
        ('bcdefghijk', 2, '{CODE_2}')""")
    db.engine.execute("UPDATE users SET locked = 't' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_hash'] = 'bcdefghijk'
    app.config['LOCKED_ACCOUNT_PERMISSIONS'] = 'view_users'

    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.get_json()['response']['id'] == 1


@pytest.mark.parametrize(
    'bytes_', [0, 9999999929313993]
    )
def test_ration_bytes_validator(bytes_):
    assert bytes_ == ration_bytes(bytes_)


@pytest.mark.parametrize(
    'bytes_', ['0', 1234567890123456789012]
    )
def test_ration_bytes_validator_fail(bytes_):
    with pytest.raises(Invalid) as e:
        ration_bytes(bytes_)
    assert str(e.value) == 'number must be a valid <20 digit bytes count'


@pytest.mark.parametrize(
    'schema', [
        {'email': 'new@ema.il'},
        {'email': 'new@ema.il', 'password': 'abcdefGHIfJK12#'},
        {'downloaded': 123123123},
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
