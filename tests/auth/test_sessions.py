import json
import pytest
from conftest import CODE_1, CODE_2, CODE_3, check_json_response, add_permissions
from pulsar import db
from pulsar.auth.models import Session


def hex_generator(_):
    return next(HEXES)


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO sessions (user_id, hash, csrf_token, active) VALUES
        (1, 'abcdefghij', '{CODE_1}', 't'),
        (2, '1234567890', '{CODE_2}', 'f')
        """)


def test_new_session(app):
    with app.app_context():
        session = Session.generate_session(2, '127.0.0.2')
        assert session.ip == '127.0.0.2'
        assert session.user_id == 2


def test_session_collision(app, monkeypatch):
    global HEXES
    HEXES = iter([CODE_2[:10], CODE_3[:10], CODE_3])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    with app.app_context():
        session = Session.generate_session(2, '127.0.0.2')
        assert session.hash != CODE_2[:10]
        assert session.csrf_token != CODE_2
        with pytest.raises(StopIteration):
            hex_generator(None)


def test_from_hash(app):
    with app.app_context():
        session = Session.from_hash('abcdefghij')
        assert session.user.id == 1
        assert session.csrf_token == CODE_1


def test_from_hash_incl_dead(app):
    with app.app_context():
        session = Session.from_hash('1234567890', include_dead=True)
        assert session.csrf_token == CODE_2


def test_get_nonexistent_session(app):
    with app.app_context():
        session = Session.from_hash('1234567890')
        assert not session


def test_session_revoke_all(app):
    with app.app_context():
        Session.expire_all_of_user(1)
        api_key = Session.from_hash('abcdefghij', include_dead=True)
        assert not api_key.active


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_sessions_schema(input_):
    from pulsar.auth.views.sessions import view_all_sessions_schema
    assert view_all_sessions_schema({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_sessions_schema_failure(input_):
    from voluptuous import MultipleInvalid
    from pulsar.auth.views.sessions import view_all_sessions_schema
    with pytest.raises(MultipleInvalid):
        assert not view_all_sessions_schema({'include_dead': input_})


@pytest.mark.parametrize(
    'session, expected', [
        ('abcdefghij', {'hash': 'abcdefghij', 'active': True}),
        ('1234567890', 'Session 1234567890 does not exist.'),
        ('notrealkey', 'Session notrealkey does not exist.'),
    ])
def test_view_session(app, authed_client, session, expected):
    add_permissions(app, 'view_sessions')
    response = authed_client.get(f'/sessions/{session}')
    check_json_response(response, expected)


def test_view_all_keys(app, authed_client):
    add_permissions(app, 'view_sessions')
    response = authed_client.get('/sessions')
    check_json_response(response, {
        'hash': CODE_2[:10],
        }, list_=True)


def test_view_empty_sessions(app, authed_client):
    add_permissions(app, 'view_sessions', 'view_sessions_others')
    response = authed_client.get(
        '/sessions/user/2', query_string=dict(include_dead=False))
    check_json_response(response, [], list_=True, strict=True)


@pytest.mark.parametrize(
    'identifier, message', [
        ('abcdefghij', 'Session abcdefghij has been revoked.'),
        ('1234567890', 'Session 1234567890 is already revoked.'),
        ('nonexisten', 'Session nonexisten does not exist.'),
    ])
def test_revoke_session(app, authed_client, identifier, message):
    add_permissions(app, 'revoke_sessions', 'revoke_sessions_others')
    response = authed_client.delete('/sessions', data=json.dumps(dict(
        identifier=identifier)))
    check_json_response(response, message)


def test_revoke_session_not_mine(app, authed_client):
    add_permissions(app, 'revoke_sessions')
    response = authed_client.delete('/sessions', data=json.dumps(dict(
        identifier='1234567890')))
    check_json_response(response, 'Session 1234567890 does not exist.')


@pytest.mark.parametrize(
    'endpoint', [
        '/sessions/all',
        '/sessions/all/user/2',
    ])
def test_revoke_all_sessions(app, authed_client, endpoint):
    add_permissions(app, 'revoke_sessions', 'revoke_sessions_others')
    response = authed_client.delete(endpoint)
    check_json_response(response, 'All sessions have been revoked.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/sessions/123', 'GET'),
        ('/sessions', 'GET'),
        ('/sessions', 'DELETE'),
        ('/sessions/all', 'DELETE'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    assert response.status_code == 404
    check_json_response(response, 'Resource does not exist.')
