import flask
import pytest

from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.utils import assert_permission, assert_user, choose_user


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        """INSERT INTO users_permissions (user_id, permission) VALUES
        (1, 'sample_perm_one'),
        (1, 'sample_perm_two'),
        (1, 'sample_perm_three')
        """)


@pytest.mark.parametrize(
    'endpoint, result', [
        ('1/sample_permission', True),
        ('2/sample_permission', True),
        ('1', True),
        ('1/nonexistent_permission', True),
        ('2/nonexistent_permission', False),
        ('2', False),
    ])
def test_assert_user(app, authed_client, endpoint, result):
    add_permissions(app, 'sample_permission')

    @app.route('/assert_user_test/<int:user_id>')
    @app.route('/assert_user_test/<int:user_id>/<permission>')
    def assert_user_test(user_id, permission=None):
        assert result == bool(assert_user(user_id, permission))
        return flask.jsonify('completed')

    response = authed_client.get(f'/assert_user_test/{endpoint}')
    check_json_response(response, 'completed')


@pytest.mark.parametrize(
    'permission, masquerade, expected', [
        ('sample_perm_one', False, 'Endpoint reached.'),
        ('not_a_real_perm', True, 'Resource does not exist.'),
        ('not_a_real_perm', False,
         'You do not have permission to access this resource.'),
    ])
def test_assert_permission(app, authed_client, permission, masquerade, expected):
    @app.route('/test_assert_perm')
    def assert_perm():
        assert_permission(permission, masquerade=masquerade)
        return flask.jsonify('Endpoint reached.')

    response = authed_client.get('/test_assert_perm')
    check_json_response(response, expected)


def test_choose_user(app, authed_client):
    @app.route('/test_choose_user')
    def test_choose_user():
        choose_user(1, 'non-existent-perm')
        choose_user(2, 'sample_perm_one')
        return flask.jsonify('Endpoint reached.')

    response = authed_client.get('/test_choose_user')
    check_json_response(response, 'Endpoint reached.')


def test_choose_user_fail(app, authed_client):
    @app.route('/test_choose_user')
    def test_choose_user():
        choose_user(2, 'non-existent-perm')
        return flask.jsonify('Endpoint reached.')

    response = authed_client.get('/test_choose_user')
    check_json_response(response, 'You do not have permission to access this resource.')
