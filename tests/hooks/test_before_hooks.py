import json
import flask
import pytest
from collections import namedtuple, defaultdict
from voluptuous import Schema, Optional
from conftest import CODE_1, CODE_2, add_permissions, check_json_response
from pulsar import db, cache, APIException
from pulsar.models import User, Session
from pulsar.utils import validate_data, require_permission


def cache_num_iter(*args, **kwargs):
    return next(CACHE_NUM)


def test_user_session_auth(app, client):
    @app.route('/test_sess')
    @require_permission('test_perm')
    def test_session():
        assert flask.g.user_session.id == 'abcdefghij'
        assert flask.g.user_session.user_agent == 'pulsar-test-client'
        assert flask.g.user_session.ip == '127.0.0.1'
        assert flask.g.user.id == 1
        assert not flask.g.api_key
        return flask.jsonify('completed')

    add_permissions(app, 'test_perm')
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'
    response = client.get('/test_sess', environ_base={
        'HTTP_USER_AGENT': 'pulsar-test-client',
        'REMOTE_ADDR': '127.0.0.1',
        })
    check_json_response(response, 'completed')
    session = Session.from_id('abcdefghij')
    assert session.user_agent == 'pulsar-test-client'


def test_session_auth_and_ip_override(app, client):
    @app.route('/test_sess')
    @require_permission('no_ip_history')
    def test_session():
        assert flask.g.user_session.ip == '0.0.0.0'
        assert flask.g.user.id == 1
        assert not flask.g.api_key
        return flask.jsonify('completed')

    add_permissions(app, 'no_ip_history')
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'
    response = client.get('/test_sess', environ_base={
        'HTTP_USER_AGENT': 'pulsar-test-client',
        'REMOTE_ADDR': '127.0.0.1',
        })
    check_json_response(response, 'completed')
    session = Session.from_id('abcdefghij')
    assert session.user_agent == 'pulsar-test-client'


@pytest.mark.parametrize(
    'user_id, session_id', [
        ('testings', 'abcdefghij'),
        ('1', 'notarealkey'),
    ])
def test_user_bad_session(app, client, user_id, session_id):
    @app.route('/test_sess')
    @require_permission('test_perm')
    def test_session():
        return flask.jsonify('completed')

    add_permissions(app, 'test_perm')
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['session_id'] = session_id
    response = client.get('/test_sess')
    check_json_response(response, 'Resource does not exist.')


def test_user_expired_session(app, client):
    @app.route('/test_sess')
    @require_permission('test_perm')
    def test_session():
        return flask.jsonify('completed')

    add_permissions('test_perm')
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = '1234567890'
    response = client.get('/test_sess')
    check_json_response(response, 'Resource does not exist.')


def test_api_key_auth_and_ip_override(app, client):
    add_permissions(app, 'no_ip_history')

    @app.route('/test_api_key')
    def test_api_key():
        assert flask.g.api_key.id == 'abcdefghij'
        assert flask.g.api_key.user_agent == ''
        assert flask.g.api_key.ip == '0.0.0.0'
        assert flask.g.user.id == 1
        assert not flask.g.user_session
        return flask.jsonify('completed')

    response = client.get('/test_api_key', environ_base={
            'HTTP_USER_AGENT': '',
            'REMOTE_ADDR': '127.0.0.1',
        }, headers={
            'Authorization': f'Token abcdefghij{CODE_1}',
        })
    check_json_response(response, 'completed')


def test_auth_updates(app, client):
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
    response = client.get('/users/1', headers={
        'Authorization': authorization_header})
    check_json_response(response, 'Resource does not exist.')


def test_csrf_validation(app, client):
    @app.route('/test_csrf', methods=['POST'])
    @validate_data(Schema({
        Optional('csrf_token', default='NonExistent'): str,
        }))
    def test_csrf(csrf_token):
        assert csrf_token == 'NonExistent'
        return flask.jsonify('completed')

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'

    response = client.post('/test_csrf', data=json.dumps({'csrf_token': CODE_1}))
    resp_data = response.get_json()
    assert 'csrf_token' in resp_data and resp_data['csrf_token'] == CODE_1
    check_json_response(response, 'completed')


def test_unneeded_csrf_validation(app, client):
    @app.route('/test_csrf', methods=['POST'])
    def test_csrf():
        return flask.jsonify('completed')

    response = client.post('/test_csrf', headers={
        'Authorization': f'Token abcdefghij{CODE_1}'})
    resp_data = response.get_json()
    assert 'csrf_token' not in resp_data
    check_json_response(response, 'completed')


@pytest.mark.parametrize(
    'endpoint', [
        '/users/change_password',
        '/not/a/real/route',
    ])
def test_false_csrf_validation_session(app, client, endpoint):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'

    response = client.put(endpoint)
    check_json_response(response, 'Invalid authorization key.')


@pytest.mark.parametrize(
    'endpoint', [
        '/users/change_password',
        '/not/a/real/route',
    ])
def test_no_authorization_post(app, client, endpoint):
    response = client.put(endpoint)
    check_json_response(response, 'Resource does not exist.')


def test_bad_data(app, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'

    response = client.post('/fake_endpoint', data=b'{a malformed ",json"}')
    check_json_response(response, 'Malformed input. Is it JSON?')


def test_disabled_user(app, client):
    db.engine.execute("UPDATE users SET enabled = 'f' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_id'] = 'bcdefghijk'

    response = client.get('/fake_endpoint')
    check_json_response(response, 'Your account has been disabled.')


def test_rate_limit_fail(app, client, monkeypatch):
    monkeypatch.setattr('pulsar.hooks.before.cache.inc', lambda *a, **k: 51)
    monkeypatch.setattr('pulsar.hooks.before.cache.ttl', lambda *a, **k: 7)
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'

    response = client.get('/fake_endpoint')
    check_json_response(response, 'Client rate limit exceeded. 7 seconds until lock expires.')


def test_rate_limit_user_fail(app, client, monkeypatch):
    global CACHE_NUM
    CACHE_NUM = iter([2, 91])
    monkeypatch.setattr('pulsar.hooks.before.cache.inc', cache_num_iter)
    monkeypatch.setattr('pulsar.hooks.before.cache.ttl', lambda *a, **k: 7)
    response = client.get('/fake_endpoint', headers={
        'Authorization': f'Token abcdefghij{CODE_1}',
        })
    check_json_response(response, 'User rate limit exceeded. 7 seconds until lock expires.')


g = namedtuple('g', ['user', 'user_session', 'api_key', 'cache_keys'])
api_key = namedtuple('APIKey', ['id'])


def test_rate_limit_function(app, client, monkeypatch):
    from pulsar.hooks.before import check_rate_limit
    monkeypatch.setattr('pulsar.hooks.before.flask.g', g(
        user=User.from_id(1),
        user_session=None,
        api_key=api_key(id='abcdefghij'),
        cache_keys=defaultdict(set),
        ))
    with pytest.raises(APIException) as e:
        for i in range(62):
            check_rate_limit()
    assert 'Client rate limit exceeded.' in e.value.message


def test_rate_limit_function_global(app, client, monkeypatch):
    from pulsar.hooks.before import check_rate_limit
    monkeypatch.setattr('pulsar.hooks.before.flask.g', g(
        user=User.from_id(1),
        user_session=None,
        api_key=api_key(id='abcdefghij'),
        cache_keys=defaultdict(set),
        ))
    cache.set('rate_limit_user_1', 70, timeout=60)
    with pytest.raises(APIException) as e:
        for i in range(31):
            check_rate_limit()
    assert 'User rate limit exceeded.' in e.value.message
