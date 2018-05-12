import json
import flask
import pytest
from conftest import CODE_1, add_permissions
from pulsar import db
from pulsar.models import User


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO sessions (hash, user_id, csrf_token) VALUES
        ('abcdefghij', 1, '{CODE_1}')
        """)


@pytest.mark.parametrize(
    'status_code, status', [
        (200, 'success'),
        (203, 'success'),
        (400, 'failed'),
        (404, 'failed'),
        (500, 'failed'),
    ])
def test_status_string(app, authed_client, status_code, status):
    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test'), status_code

    response = authed_client.get('/test_endpoint')
    assert json.loads(response.get_data()) == {
        'response': 'test',
        'status': status,
    }


def test_csrf_token(app, client):
    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test')

    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['session_hash'] = 'abcdefghij'

    response = client.get('/test_endpoint')
    assert json.loads(response.get_data()) == {
        'status': 'success',
        'csrf_token': CODE_1,
        'response': 'test',
        }


def test_unauthorized_csrf_token(app, client):
    app.config['SITE_PRIVATE'] = False

    @app.route('/test_endpoint')
    def test_endpoint():
        return flask.jsonify('test')

    response = client.get('/test_endpoint')
    assert json.loads(response.get_data()) == {
        'status': 'success',
        'response': 'test',
        }


def test_cache_keys(app, authed_client):
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
