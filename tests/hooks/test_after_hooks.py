import flask
import pytest

from conftest import CODE_1, add_permissions
from pulsar.models import User


@pytest.mark.parametrize(
    'status_code, status', [
        (200, 'success'),
        (203, 'success'),
        (400, 'failed'),
        (404, 'failed'),
        (500, 'failed'),
    ])
def test_status_string(app, authed_client, status_code, status):
    """The status string should populate itself based on status code."""
    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test'), status_code

    response = authed_client.get('/test_endpoint')
    assert response.get_json() == {
        'response': 'test',
        'status': status,
    }


def test_csrf_token(app, client):
    """The CSRF token should be present if the request is made by a session."""
    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test')

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_id'] = 'abcdefghij'

    response = client.get('/test_endpoint')
    assert response.get_json() == {
        'status': 'success',
        'csrf_token': CODE_1,
        'response': 'test',
        }


def test_csrf_token_no_session(app, authed_client):
    """The CSRF token should not be present if the request isn't made by a session."""
    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test')

    response = authed_client.get('/test_endpoint')
    assert 'csrf_token' not in response.get_json()


def test_cache_keys(app, authed_client):
    """
    Cache keys should be included in the response if user has
    view_cache_keys permission.
    """
    add_permissions(app, 'view_cache_keys')

    @app.route('/test_endpoint')
    def test_endpoint():
        _ = User.from_id(2)  # noqa
        return flask.jsonify('test')

    response = authed_client.get('/test_endpoint')
    data = response.get_json()
    assert 'set' in data['cache_keys']
    assert 'users_1_permissions' in data['cache_keys']['set']
    assert 'users_2' in data['cache_keys']['set']


def test_cache_keys_no_perms(app, authed_client):
    """
    Cache keys should not be included in the response if user does not have
    view_cache_keys permission.
    """
    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test')

    response = authed_client.get('/test_endpoint')
    assert 'cache_keys' not in response.get_json()
