import json

import flask
from voluptuous import Schema

from conftest import check_json_response
from pulsar.utils import validate_data


def test_invalid_schema(app, authed_client):
    @app.route('/test_schema', methods=['POST'])
    @validate_data(Schema({
        'required_arg': int}))
    def test_schema(required_arg):
        return 'never hit this'

    response = authed_client.post(
        '/test_schema', data=json.dumps({'required_arg': 'not-an-int'}))
    check_json_response(response, 'Invalid data: expected int (key "required_arg")')


def test_invalid_json(app, authed_client):
    @app.route('/test_endpoint', methods=['POST'])
    @validate_data(Schema({'test': int}))
    def test_endpoint():
        return flask.jsonify('completed')
    response = authed_client.post('/test_endpoint', data=b'not-a-json')
    check_json_response(
        response, 'Unable to decode data. Is it valid JSON.')
