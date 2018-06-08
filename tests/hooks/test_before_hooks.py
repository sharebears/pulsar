from collections import defaultdict, namedtuple

import flask
import pytest
from voluptuous import Schema

from conftest import CODE_1, CODE_2, add_permissions, check_json_response
from pulsar import APIException, cache, db
from pulsar.hooks.before import check_rate_limit
from pulsar.users.models import User
from pulsar.utils import require_permission, validate_data


def cache_num_iter(*args, **kwargs):
    return next(CACHE_NUM)


def test_api_key_auth_and_ip_override(app, client):
    """User and APIKey IP should be overridden with IP history override permissions."""
    add_permissions(app, 'no_ip_history')

    @app.route('/test_api_key')
    def test_api_key():
        assert flask.g.api_key.hash == 'abcdefghij'
        assert flask.g.api_key.user_agent == ''
        assert flask.g.api_key.ip == '0.0.0.0'
        assert flask.g.user.id == 1
        return flask.jsonify('completed')

    response = client.get('/test_api_key', environ_base={
            'HTTP_USER_AGENT': '',
            'REMOTE_ADDR': '127.0.0.1',
        }, headers={
            'Authorization': f'Token abcdefghij{CODE_1}',
        })
    check_json_response(response, 'completed')


def test_auth_updates(app, client):
    """Test that the cache key delay for updating an API key works."""
    @app.route('/test_api_key')
    def test_api_key():
        return flask.jsonify('completed')

    db.engine.execute(
        "UPDATE api_keys SET ip = '127.0.0.1', user_agent = 'pulsar-test-client'")
    cache.set('api_keys_abcdefghij_updated', 1, timeout=9000)
    response = client.get('/test_api_key', environ_base={
            'HTTP_USER_AGENT': 'pulsar-test-client',
            'REMOTE_ADDR': '127.0.0.1',
        }, headers={
            'Authorization': f'Token abcdefghij{CODE_1}',
        })
    check_json_response(response, 'completed')
    assert cache.ttl('api_keys_abcdefghij_updated') > 8000


@pytest.mark.parametrize(
    'authorization_header', [
        'Token abcdefgnotarealone',
        'Token abcdefghij123456789012345678901234',
        'Token 1234567',
        'TokenMalformed',
        f'Token 1234567890{CODE_2}',
    ])
def test_user_bad_api_key(app, client, authorization_header):
    """Assert that a bad or expired API key raises a 404."""
    response = client.get('/users/1', headers={
        'Authorization': authorization_header})
    check_json_response(response, 'Invalid authorization.')


@pytest.mark.parametrize(
    'endpoint', [
        '/users/change_password',
        '/not/a/real/route',
    ])
def test_no_authorization_post(app, client, endpoint):
    """Assert that checking an endpoint without authentication throws a 401."""
    response = client.put(endpoint)
    check_json_response(response, 'Invalid authorization.')


def test_403_masquerade(app, client):
    """Masqueraded 403 endpoints should throw 404s."""
    @app.route('/test_endpoint')
    @require_permission('test_perm', masquerade=True)
    def test_session():
        return flask.jsonify('completed')

    response = client.get('/test_endpoint', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'
        })
    check_json_response(response, 'Resource does not exist.')


def test_403_masquerade_no_auth(app, client):
    """Masqueraded 403 endpoints should throw 401s without authentication."""
    @app.route('/test_endpoint')
    @require_permission('test_perm', masquerade=True)
    def test_session():
        return flask.jsonify('completed')

    response = client.get('/test_endpoint')
    check_json_response(response, 'Invalid authorization.')


def test_bad_data(app, client):
    """Assert that bad request data raises an error."""
    @app.route('/fake_endpoint', methods=['POST'])
    @validate_data(Schema({'a': str}))
    def fake_endpoint():
        pass

    response = client.post(
        '/fake_endpoint',
        data=b'{a malformed ",json"}',
        headers={'Authorization': f'Token abcdefghij{CODE_1}'}
        )
    check_json_response(response, 'Unable to decode data. Is it valid JSON?')


def test_disabled_user(app, client):
    """Disabled users get disabled errors."""
    db.engine.execute("UPDATE users SET enabled = 'f' where id = 1")
    response = client.get('/fake_endpoint', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'
        })
    check_json_response(response, 'Your account has been disabled.')


def test_rate_limit_fail(app, client, monkeypatch):
    """Exceeding the per-key rate limit should return a failure message."""
    monkeypatch.setattr('pulsar.hooks.before.cache.inc', lambda *a, **k: 51)
    monkeypatch.setattr('pulsar.hooks.before.cache.ttl', lambda *a, **k: 7)
    response = client.get('/fake_endpoint', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'
        })
    check_json_response(response, 'Client rate limit exceeded. 7 seconds until lock expires.')


def test_rate_limit_user_fail(app, client, monkeypatch):
    """Exceeding the per-user rate limit should return a failure message."""
    global CACHE_NUM
    CACHE_NUM = iter([2, 91])
    monkeypatch.setattr('pulsar.hooks.before.cache.inc', cache_num_iter)
    monkeypatch.setattr('pulsar.hooks.before.cache.ttl', lambda *a, **k: 7)
    response = client.get('/fake_endpoint', headers={
        'Authorization': f'Token abcdefghij{CODE_1}',
        })
    check_json_response(response, 'User rate limit exceeded. 7 seconds until lock expires.')


g = namedtuple('g', ['user', 'api_key', 'cache_keys'])
api_key = namedtuple('APIKey', ['hash'])


def test_rate_limit_function(app, client, monkeypatch):
    """Test that the per-key rate limit function correctly increments and errors."""
    monkeypatch.setattr('pulsar.hooks.before.flask.g', g(
        user=User.from_pk(1),
        api_key=api_key(hash='abcdefghij'),
        cache_keys=defaultdict(set),
        ))
    with pytest.raises(APIException) as e:
        for i in range(62):
            check_rate_limit()
    assert 'Client rate limit exceeded.' in e.value.message


def test_rate_limit_function_global(app, client, monkeypatch):
    """Test that the per-user rate limit function correctly increments and errors."""
    monkeypatch.setattr('pulsar.hooks.before.flask.g', g(
        user=User.from_pk(1),
        api_key=api_key(hash='abcdefghij'),
        cache_keys=defaultdict(set),
        ))
    cache.set('rate_limit_user_1', 70, timeout=60)
    with pytest.raises(APIException) as e:
        for i in range(31):
            check_rate_limit()
    assert 'User rate limit exceeded.' in e.value.message
