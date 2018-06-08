import json

import flask
import pytest

from conftest import CODE_1, CODE_2, CODE_3, add_permissions, check_json_response
from pulsar import cache
from pulsar.auth.models import APIKey
from pulsar.utils import require_permission


def hex_generator(_):
    return next(HEXES)


@pytest.mark.parametrize(
    'key, expected', [
        ('abcdefghij', {'hash': 'abcdefghij', 'revoked': False}),
        ('1234567890', 'APIKey 1234567890 does not exist.'),
        ('notrealkey', 'APIKey notrealkey does not exist.'),
    ])
def test_view_api_key(app, authed_client, key, expected):
    add_permissions(app, 'view_api_keys')
    response = authed_client.get(f'/api_keys/{key}')
    check_json_response(response, expected)


def test_view_api_key_other(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    response = authed_client.get(f'/api_keys/1234567890')
    check_json_response(response, {'hash': '1234567890', 'revoked': True})


def test_view_api_key_cached(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    api_key = APIKey.from_pk('1234567890', include_dead=True)
    cache_key = cache.cache_model(api_key, timeout=60)

    response = authed_client.get(f'/api_keys/1234567890')
    check_json_response(response, {'hash': '1234567890', 'revoked': True})
    assert cache.ttl(cache_key) < 61


def test_view_all_keys(app, authed_client):
    add_permissions(app, 'view_api_keys')
    response = authed_client.get('/api_keys')
    data = response.get_json()['response']
    assert any('hash' in api_key and api_key['hash'] == CODE_2[:10]
               for api_key in data)


def test_view_all_keys_cached(app, authed_client):
    add_permissions(app, 'view_api_keys')
    cache_key = APIKey.__cache_key_of_user__.format(user_id=1)
    cache.set(cache_key, ['abcdefghij', 'bcdefghijk'], timeout=60)

    response = authed_client.get('/api_keys')
    data = response.get_json()['response']
    assert any('hash' in api_key and api_key['hash'] == CODE_2[:10]
               for api_key in data)
    assert cache.ttl(cache_key)


def test_view_empty_api_keys(app, authed_client):
    add_permissions(app, 'view_api_keys', 'view_api_keys_others')
    response = authed_client.get(
        '/api_keys/user/2', query_string={'include_dead': False})
    check_json_response(response, [], list_=True, strict=True)


def test_create_api_key(app, client, monkeypatch):
    global HEXES
    HEXES = iter(['a' * 8, 'a' * 16])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    response = client.post('/api_keys', data=json.dumps({
        'username': 'lights', 'password': '12345'}))
    check_json_response(response, {'key': 'a' * 24})
    with pytest.raises(StopIteration):
        hex_generator(None)


def test_create_api_key_with_permissions(app, authed_client, monkeypatch):
    global HEXES
    HEXES = iter(['a' * 8, 'a' * 16])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    authed_client.post('/api_keys', data=json.dumps({
        'permissions': ['sample_perm_one', 'sample_perm_two']}),
        content_type='application/json')
    key = APIKey.from_pk('a' * 8)
    assert key.has_permission('sample_perm_one')
    assert key.has_permission('sample_perm_two')
    assert not key.has_permission('sample_perm_three')


@pytest.mark.parametrize(
    'identifier, message', [
        ('abcdefghij', 'APIKey abcdefghij has been revoked.'),
        ('1234567890', 'APIKey 1234567890 is already revoked.'),
        ('\x02\xb0\xc0AZ\xf2\x99\x22\x8b\xdc',
         'APIKey \x02\xb0\xc0AZ\xf2\x99\x22\x8b\xdc does not exist.'),
    ])
def test_revoke_api_key(app, authed_client, identifier, message):
    add_permissions(app, 'revoke_api_keys', 'revoke_api_keys_others')
    response = authed_client.delete('/api_keys', data=json.dumps({'hash': identifier}))
    check_json_response(response, message)


def test_revoke_api_key_not_mine(app, authed_client):
    add_permissions(app, 'revoke_api_keys')
    response = authed_client.delete('/api_keys', data=json.dumps({'hash': '1234567890'}))
    check_json_response(response, 'APIKey 1234567890 does not exist.')


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
        response, 'This APIKey does not have permission to access this resource.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/api_keys/123', 'GET'),
        ('/api_keys', 'GET'),
        ('/api_keys', 'DELETE'),
        ('/api_keys/all', 'DELETE'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
