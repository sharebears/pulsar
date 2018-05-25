import json

import pytest

from conftest import CODE_2, add_permissions, check_json_response


@pytest.mark.parametrize(
    'session, expected', [
        ('abcdefghij', {'hash': 'abcdefghij', 'expired': False}),
        ('1234567890', 'Session 1234567890 does not exist.'),
        ('notrealkey', 'Session notrealkey does not exist.'),
    ])
def test_view_session(app, authed_client, session, expected):
    add_permissions(app, 'view_sessions')
    response = authed_client.get(f'/sessions/{session}')
    check_json_response(response, expected)


def test_view_all_sessions(app, authed_client):
    add_permissions(app, 'view_sessions')
    response = authed_client.get('/sessions')
    check_json_response(response, {
        'hash': CODE_2[:10],
        }, list_=True)


def test_view_empty_sessions(app, authed_client):
    add_permissions(app, 'view_sessions', 'view_sessions_others')
    response = authed_client.get(
        '/sessions/user/2', query_string={'include_dead': False})
    check_json_response(response, [], list_=True, strict=True)


def test_create_session_success(client):
    response = client.post('/sessions', data=json.dumps({
        'username': 'lights', 'password': '12345'}))
    response_data = response.get_json()
    assert response_data['response']['expired'] is False
    assert 'ip' in response_data['response'] and 'hash' in response_data['response']
    with client.session_transaction() as sess:
        assert 'user_id' in sess and 'session_hash' in sess


def test_create_session_success_cached_sessions(client):
    response = client.post('/sessions', data=json.dumps({
        'username': 'lights', 'password': '12345'}))
    response_data = response.get_json()
    assert response_data['response']['expired'] is False
    assert 'ip' in response_data['response'] and 'hash' in response_data['response']
    with client.session_transaction() as sess:
        assert 'user_id' in sess and 'session_hash' in sess


def test_create_session_persistent(client):
    response = client.post('/sessions', data=json.dumps({
        'username': 'lights',
        'password': '12345',
        'persistent': True,
        }))
    response_data = response.get_json()

    assert response_data['response']['persistent'] is True


def test_create_session_failure(client):
    response = client.post('/sessions', data=json.dumps({
        'username': 'not_lights', 'password': '54321'}))

    check_json_response(response, 'Invalid credentials.')
    assert response.status_code == 401


@pytest.mark.parametrize(
    'identifier, message', [
        ('abcdefghij', 'Session abcdefghij has been expired.'),
        ('1234567890', 'Session 1234567890 is already expired.'),
        ('nonexisten', 'Session nonexisten does not exist.'),
    ])
def test_expire_session(app, authed_client, identifier, message):
    add_permissions(app, 'expire_sessions', 'expire_sessions_others')
    response = authed_client.delete('/sessions', data=json.dumps({'hash': identifier}))
    check_json_response(response, message)


def test_expire_session_not_mine(app, authed_client):
    add_permissions(app, 'expire_sessions')
    response = authed_client.delete('/sessions', data=json.dumps({'hash': '1234567890'}))
    check_json_response(response, 'Session 1234567890 does not exist.')


@pytest.mark.parametrize(
    'endpoint', [
        '/sessions/all',
        '/sessions/all/user/2',
    ])
def test_expire_all_sessions(app, authed_client, endpoint):
    add_permissions(app, 'expire_sessions', 'expire_sessions_others')
    response = authed_client.delete(endpoint)
    check_json_response(response, 'All sessions have been expired.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/sessions/123', 'GET'),
        ('/sessions', 'GET'),
        ('/sessions', 'DELETE'),
        ('/sessions/all', 'DELETE'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    assert response.status_code == 403
    check_json_response(response, 'You do not have permission to access this resource.')
