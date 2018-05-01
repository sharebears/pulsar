import flask
import pytest
from voluptuous import Schema, Invalid
from conftest import check_json_response
from pulsar.utils import bool_get, validate_data


def test_invalid_schema(app, authed_client):
    @app.route('/test_schema', methods=['POST'])
    @validate_data(Schema({
        'required_arg': int}))
    def test_schema(required_arg):
        return 'never hit this'

    response = authed_client.post('/test_schema', json={'required_arg': 'not-an-int'})
    check_json_response(response, 'Invalid data: expected int (key "required_arg")')


@pytest.mark.parametrize(
    'inputs, output', [
        ([True, '1', 'TruE', 'true'], True),
        ([False, '0', 'FaLsE', 'false'], False),
    ])
def test_bool_get(inputs, output):
    for input_ in inputs:
        assert output == bool_get(input_)


def test_bool_get_invalid():
    for input_ in [1, 0, 'Yes', 'No', '11']:
        with pytest.raises(Invalid):
            bool_get(input_)


def test_invalid_json(app, authed_client):
    @app.route('/test_endpoint', methods=['POST'])
    @validate_data(Schema({'test': int}))
    def test_endpoint():
        return flask.jsonify('completed')
    response = authed_client.post('/test_endpoint', data=b'not-a-json')
    check_json_response(
        response, 'Unable to decode data. Please make sure you are sending valid JSON.')
