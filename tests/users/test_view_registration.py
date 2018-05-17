import json

import pytest

from conftest import CODE_1, CODE_2, CODE_3, check_json_response


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


def test_registration_no_code(app, client):
    app.config['REQUIRE_INVITE_CODE'] = True
    response = client.post('/register', data=json.dumps({
        'username': 'abiejfaiwof',
        'password': 'abcdEF123123%',
        'email': 'bright@puls.ar'}))
    check_json_response(response, 'An invite code is required for registration.')
    assert response.status_code == 400
