import json
import flask
import pytest
from conftest import CODE_1
from pulsar import db


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
