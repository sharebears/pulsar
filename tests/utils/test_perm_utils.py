import json
import flask
import pytest
from voluptuous import Invalid
from conftest import add_permissions, check_json_response
from pulsar import db
from pulsar.utils import assert_user, assert_permission, permissions_list


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        """INSERT INTO permissions (user_id, permission) VALUES
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


@pytest.mark.parametrize(
    'permissions', [
        ['samp_perm_four', 'nonexistent_perm'],
        False,
    ])
def test_permissions_list_error(app, authed_client, permissions):
    @app.route('/test_permissions_error', methods=['POST'])
    def test_permissions_error():
        with pytest.raises(Invalid):
            data = json.loads(flask.request.get_data())
            permissions_list(data['permissions'])
        return flask.jsonify('completed')

    response = authed_client.post(
        '/test_permissions_error', data=json.dumps({'permissions': permissions}),
        content_type='application/json')
    check_json_response(response, 'completed')
