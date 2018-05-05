import json
import pytest
from voluptuous import Invalid
from conftest import CODE_1, CODE_2, CODE_3, check_json_response
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO invites (inviter_id, email, code, time_sent, active) VALUES
        (1, 'bright@puls.ar', '{CODE_1}', NOW(), 't'),
        (1, 'bitsu@puls.ar', '{CODE_2}', NOW(), 'f'),
        (1, 'bright@quas.ar', '{CODE_3}', '2018-03-25 01:09:35.260808+00', 't')
        """)
    yield
    db.engine.execute("DELETE FROM invites")


@pytest.mark.parametrize(
    'code, status_code, expected', [
        (CODE_1, 200, {'username': 'bright'}),
        (None, 400, 'Invalid data: an invite code is required for '
                    'registration (key "code")'),
        (CODE_2, 400, f'Invalid data: {CODE_2} is not a valid invite code (key "code")'),
        (CODE_3, 400, f'Invalid data: {CODE_3} is not a valid invite code (key "code")'),
    ])
def test_register_with_code(app, client, code, status_code, expected):
    app.config['REQUIRE_INVITE_CODE'] = True
    endpoint = f'/register' if code else '/register'
    response = client.post(endpoint, data=json.dumps({
        'username': 'bright',
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar',
        'code': code,
        }))
    check_json_response(response, expected, strict=True)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    'username, status_code, expected', [
        ('bright', 200, {'username': 'bright'}),
        ('lights', 400, 'Invalid data: another user already has the username '
                        'lights (key "username")'),
    ])
def test_registration(app, client, username, status_code, expected):
    app.config['REQUIRE_INVITE_CODE'] = False
    response = client.post('/register', data=json.dumps({
        'username': username,
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar'}))
    check_json_response(response, expected, strict=True)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    'username', [
        123, '1234567890abcdefghijklmnoqrstuvwxyzabcdef', None
    ])
def test_username_validation_fail(app, client, username):
    from pulsar.users.validators import val_username
    with pytest.raises(Invalid) as e:
        val_username(username)
    assert str(e.value) == (
        'usernames must start with an alphanumeric character; can only contain '
        'alphanumeric characters, underscores, hyphens, and periods; and be '
        '32 characters or less')


@pytest.mark.parametrize(
    'code, error', [
        (123, 'code must be a string'),
    ])
def test_invite_code_validation_fail(app, client, code, error):
    from pulsar.users.validators import val_invite_code
    app.config['REQUIRE_INVITE_CODE'] = True
    with pytest.raises(Invalid) as e:
        val_invite_code(code)
    assert str(e.value) == error
