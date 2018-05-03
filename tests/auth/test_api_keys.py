import json
import flask
import pytest
from conftest import (CODE_1, CODE_2, CODE_3, HASHED_CODE_1, HASHED_CODE_2,
                      HASHED_CODE_3, add_permissions, check_json_response)
from pulsar import db
from pulsar.auth.models import APIKey
from pulsar.utils import require_permission


def hex_generator(_):
    return next(HEXES)


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO api_keys (user_id, hash, keyhashsalt, active) VALUES
        (1, 'abcdefghij', '{HASHED_CODE_1}', 't'),
        (1, 'bcdefghijk', '{HASHED_CODE_3}', 't'),
        (2, '1234567890', '{HASHED_CODE_2}', 'f')
        """)
    db.engine.execute(
        """INSERT INTO api_permissions (api_key_hash, permission) VALUES
        ('abcdefghij', 'sample_permission'),
        ('abcdefghij', 'sample_2_permission'),
        ('abcdefghij', 'sample_3_permission')
        """)
    db.engine.execute(
        """INSERT INTO users_permissions (user_id, permission) VALUES
        (1, 'sample_permission'),
        (1, 'sample_perm_one'),
        (1, 'sample_perm_two')
        """)
    yield
    db.engine.execute("DELETE FROM api_permissions")
    db.engine.execute("DELETE FROM api_keys")


def test_new_key(app):
    with app.app_context():
        raw_key, api_key = APIKey.generate_key(2, '127.0.0.2', 'UA')
        assert len(raw_key) == 26
        assert api_key.ip == '127.0.0.2'
        assert api_key.user_id == 2


def test_api_key_collision(app, monkeypatch):
    # First four are the the hash and csrf_token, last one is the 16char key.
    global HEXES
    HEXES = iter([CODE_2[:10], CODE_3[:10], CODE_1[:16]])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    with app.app_context():
        raw_key, api_key = APIKey.generate_key(2, '127.0.0.2', 'UA')
        assert len(raw_key) == 26
        assert api_key.hash != CODE_2[:10]
        with pytest.raises(StopIteration):
            hex_generator(None)


def test_from_hash_and_check(app):
    with app.app_context():
        api_key = APIKey.from_hash('abcdefghij')
        assert api_key.user.id == 1
        assert api_key.check_key(CODE_1)
        assert not api_key.check_key(CODE_2)


def test_from_hash_when_dead(app):
    with app.app_context():
        api_key = APIKey.from_hash('1234567890', include_dead=True)
        assert api_key.user_id == 2
        assert api_key.check_key(CODE_2)


def test_api_key_revoke_all(app):
    with app.app_context():
        APIKey.revoke_all_of_user(1)
        api_key = APIKey.from_hash('abcdefghij', include_dead=True)
        assert not api_key.active


def test_api_key_permission(app):
    with app.app_context():
        api_key = APIKey.from_hash('abcdefghij', include_dead=True)
        assert api_key.has_permission('sample_permission')
        assert not api_key.has_permission('not_a_permission')


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_api_keys_schema(input_):
    from pulsar.auth.views.api_keys import view_all_api_keys_schema
    assert view_all_api_keys_schema({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_api_keys_schema_failure(input_):
    from voluptuous import MultipleInvalid
    from pulsar.auth.views.api_keys import view_all_api_keys_schema
    with pytest.raises(MultipleInvalid):
        assert not view_all_api_keys_schema({'include_dead': input_})


@pytest.mark.parametrize(
    'key, expected', [
        ('abcdefghij', {'hash': 'abcdefghij', 'active': True}),
        ('1234567890', 'API Key 1234567890 does not exist.'),
        ('notrealkey', 'API Key notrealkey does not exist.'),
    ])
def test_view_api_key(app, authed_client, key, expected):
    add_permissions(app, 'view_api_keys')
    response = authed_client.get(f'/api_keys/{key}')
    check_json_response(response, expected)


def test_view_all_keys(app, authed_client):
    add_permissions(app, 'view_api_keys')
    response = authed_client.get('/api_keys')
    data = response.get_json()['response']
    assert any('hash' in api_key and api_key['hash'] == CODE_2[:10]
               for api_key in data)


def test_view_empty_api_keys(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    response = authed_client.get(
        '/api_keys/user/2', query_string={'include_dead': False})
    check_json_response(response, [], list_=True, strict=True)


def test_create_api_key(app, authed_client, monkeypatch):
    global HEXES
    HEXES = iter(['a' * 8, 'a' * 16])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    add_permissions(app, 'create_api_keys')
    response = authed_client.post('/api_keys')
    check_json_response(response, {'key': 'a' * 24})
    with pytest.raises(StopIteration):
        hex_generator(None)


def test_create_api_key_with_permissions(app, authed_client, monkeypatch):
    global HEXES
    HEXES = iter(['a' * 8, 'a' * 16])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    add_permissions(app, 'create_api_keys')
    authed_client.post('/api_keys', data=json.dumps({
        'permissions': ['sample_perm_one', 'sample_perm_two']}),
        content_type='application/json')
    key = APIKey.from_hash('a' * 8)
    assert key.has_permission('sample_perm_one')
    assert key.has_permission('sample_perm_two')
    assert not key.has_permission('sample_perm_three')


@pytest.mark.parametrize(
    'identifier, message', [
        ('abcdefghij', 'API Key abcdefghij has been revoked.'),
        ('1234567890', 'API Key 1234567890 is already revoked.'),
        ('nonexisten', 'API Key nonexisten does not exist.'),
    ])
def test_revoke_api_key(app, authed_client, identifier, message):
    add_permissions(app, 'revoke_api_keys', 'revoke_api_keys_others')
    response = authed_client.delete('/api_keys', json={'identifier': identifier})
    check_json_response(response, message)


def test_revoke_api_key_not_mine(app, authed_client):
    add_permissions(app, 'revoke_api_keys')
    response = authed_client.delete('/api_keys', json={'identifier': '1234567890'})
    check_json_response(response, 'API Key 1234567890 does not exist.')


@pytest.mark.parametrize(
    'endpoint', [
        '/api_keys/all',
        '/api_keys/all/user/2',
    ])
def test_revoke_all_api_keys(app, authed_client, endpoint):
    add_permissions(app, 'revoke_api_keys', 'revoke_api_keys_others')
    response = authed_client.delete(endpoint)
    check_json_response(response, 'All api keys have been revoked.')


def test_view_resource_with_api_permission(app, client):
    @app.route('/test_restricted_resource')
    @require_permission('sample_permission')
    def test_permission():
        return flask.jsonify('completed')

    response = client.get('/test_restricted_resource', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'})
    check_json_response(response, 'completed')


def test_view_resource_with_user_permission(app, client):
    @app.route('/test_restricted_resource')
    @require_permission('sample_permission')
    def test_permission():
        return flask.jsonify('completed')

    response = client.get('/test_restricted_resource', headers={
        'Authorization': f'Token bcdefghijk{CODE_3}'})
    check_json_response(response, 'completed')


def test_view_resource_with_user_restriction(app, client):
    @app.route('/test_restricted_resource')
    @require_permission('sample_2_permission')
    def test_permission():
        return flask.jsonify('completed')
    response = client.get('/test_restricted_resource', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'})
    check_json_response(response, 'Resource does not exist.')


def test_view_resource_with_api_key_restriction(app, client):
    @app.route('/test_restricted_resource')
    @require_permission('sample_perm_one')
    def test_permission():
        return flask.jsonify('completed')

    response = client.get('/test_restricted_resource', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'})
    check_json_response(
        response, 'This API Key does not have permission to access this resource.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/api_keys/123', 'GET'),
        ('/api_keys', 'GET'),
        ('/api_keys', 'POST'),
        ('/api_keys', 'DELETE'),
        ('/api_keys/all', 'DELETE'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    assert response.status_code == 404
    check_json_response(response, 'Resource does not exist.')
