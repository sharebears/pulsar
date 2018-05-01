import pytest
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
        (None, 400, 'An invite code is required for registration.'),
        (CODE_2, 400, f'{CODE_2} is not a valid invite code.'),
        (CODE_3, 400, f'{CODE_3} is not a valid invite code.'),
    ])
def test_register_with_code(app, client, code, status_code, expected):
    app.config['REQUIRE_INVITE_CODE'] = True
    endpoint = f'/register' if code else '/register'
    response = client.post(endpoint, json={
        'username': 'bright',
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar',
        'code': code,
        })
    check_json_response(response, expected, strict=True)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    'username, status_code, expected', [
        ('bright', 200, {'username': 'bright'}),
        ('lights', 400, 'Another user already has the username lights.'),
    ])
def test_registration(app, client, username, status_code, expected):
    app.config['REQUIRE_INVITE_CODE'] = False
    response = client.post('/register', json={
        'username': username,
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar'})
    check_json_response(response, expected, strict=True)
    assert response.status_code == status_code
