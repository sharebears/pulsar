import json
import flask
import pytest
from conftest import CODE_1, CODE_2, CODE_3, add_permissions, check_json_response
from pulsar import db, cache
from pulsar.models import APIKey
from pulsar.utils import require_permission


def hex_generator(_):
    return next(HEXES)


def test_new_key(app, client):
    raw_key, api_key = APIKey.new(2, '127.0.0.2', 'UA')
    assert len(raw_key) == 26
    assert api_key.ip == '127.0.0.2'
    assert api_key.user_id == 2


def test_api_key_collision(app, client, monkeypatch):
    # First four are the the id and csrf_token, last one is the 16char key.
    global HEXES
    HEXES = iter([CODE_2[:10], CODE_3[:10], CODE_1[:16]])
    monkeypatch.setattr('pulsar.models.secrets.token_hex', hex_generator)

    raw_key, api_key = APIKey.new(2, '127.0.0.2', 'UA')
    assert len(raw_key) == 26
    assert api_key.id != CODE_2[:10]
    with pytest.raises(StopIteration):
        hex_generator(None)


def test_from_id_and_check(app, client):
    api_key = APIKey.from_id('abcdefghij')
    assert api_key.user_id == 1
    assert api_key.check_key(CODE_1)
    assert not api_key.check_key(CODE_2)


def test_from_id_when_dead(app, client):
    api_key = APIKey.from_id('1234567890', include_dead=True)
    assert api_key.user_id == 2
    assert api_key.check_key(CODE_2)


def test_api_key_revoke_all(app, client):
    APIKey.revoke_all_of_user(1)
    db.session.commit()
    api_key = APIKey.from_id('abcdefghij', include_dead=True)
    assert api_key.revoked


def test_api_key_revoke_all_cache(client):
    api_key = APIKey.from_id('abcdefghij')
    cache_key = cache.cache_model(api_key, timeout=60)
    assert cache.ttl(cache_key) < 61
    APIKey.revoke_all_of_user(1)
    db.session.commit()
    api_key = APIKey.from_id('abcdefghij', include_dead=True)
    assert api_key.revoked is True
    assert cache.ttl(cache_key) > 61


def test_api_key_permission(app, client):
    api_key = APIKey.from_id('abcdefghij', include_dead=True)
    assert api_key.has_permission('sample_permission')
    assert not api_key.has_permission('not_a_permission')


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_api_keys_schema(input_):
    from pulsar.auth.api_keys import view_all_api_keys_schema
    assert view_all_api_keys_schema({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_api_keys_schema_failure(input_):
    from voluptuous import MultipleInvalid
    from pulsar.auth.api_keys import view_all_api_keys_schema
    with pytest.raises(MultipleInvalid):
        assert not view_all_api_keys_schema({'include_dead': input_})


@pytest.mark.parametrize(
    'key, expected', [
        ('abcdefghij', {'id': 'abcdefghij', 'revoked': False}),
        ('1234567890', 'API Key 1234567890 does not exist.'),
        ('notrealkey', 'API Key notrealkey does not exist.'),
    ])
def test_view_api_key(app, authed_client, key, expected):
    add_permissions(app, 'view_api_keys')
    response = authed_client.get(f'/api_keys/{key}')
    check_json_response(response, expected)


def test_view_api_key_other(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    response = authed_client.get(f'/api_keys/1234567890')
    check_json_response(response, {'id': '1234567890', 'revoked': True})


def test_view_api_key_cached(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    api_key = APIKey.from_id('1234567890', include_dead=True)
    cache_key = cache.cache_model(api_key, timeout=60)

    response = authed_client.get(f'/api_keys/1234567890')
    check_json_response(response, {'id': '1234567890', 'revoked': True})
    assert cache.ttl(cache_key) < 61


def test_view_all_keys(app, authed_client):
    add_permissions(app, 'view_api_keys')
    response = authed_client.get('/api_keys')
    data = response.get_json()['response']
    assert any('id' in api_key and api_key['id'] == CODE_2[:10]
               for api_key in data)


def test_view_all_keys_cached(app, authed_client):
    add_permissions(app, 'view_api_keys')
    cache_key = APIKey.__cache_key_of_user__.format(user_id=1)
    cache.set(cache_key, ['abcdefghij', 'bcdefghijk'], timeout=60)

    response = authed_client.get('/api_keys')
    data = response.get_json()['response']
    assert any('id' in api_key and api_key['id'] == CODE_2[:10]
               for api_key in data)
    assert cache.ttl(cache_key)


def test_view_empty_api_keys(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    response = authed_client.get(
        '/api_keys/user/2', query_string={'include_dead': False})
    check_json_response(response, [], list_=True, strict=True)


def test_create_api_key(app, authed_client, monkeypatch):
    global HEXES
    HEXES = iter(['a' * 8, 'a' * 16])
    monkeypatch.setattr('pulsar.models.secrets.token_hex', hex_generator)
    add_permissions(app, 'create_api_keys')
    response = authed_client.post('/api_keys')
    check_json_response(response, {'key': 'a' * 24})
    with pytest.raises(StopIteration):
        hex_generator(None)


def test_create_api_key_with_permissions(app, authed_client, monkeypatch):
    global HEXES
    HEXES = iter(['a' * 8, 'a' * 16])
    monkeypatch.setattr('pulsar.models.secrets.token_hex', hex_generator)
    add_permissions(app, 'create_api_keys')
    authed_client.post('/api_keys', data=json.dumps({
        'permissions': ['sample_perm_one', 'sample_perm_two']}),
        content_type='application/json')
    key = APIKey.from_id('a' * 8)
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
    response = authed_client.delete('/api_keys', data=json.dumps({'id': identifier}))
    check_json_response(response, message)


def test_revoke_api_key_not_mine(app, authed_client):
    add_permissions(app, 'revoke_api_keys')
    response = authed_client.delete('/api_keys', data=json.dumps({'id': '1234567890'}))
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
    check_json_response(response, 'You do not have permission to access this resource.')


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
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
