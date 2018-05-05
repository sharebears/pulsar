import json
import pytest
from voluptuous import Invalid
from conftest import check_json_response
from pulsar.auth.views.login import login_schema


def test_login_success(client):
    response = client.post('/login', data=json.dumps({
        'username': 'lights', 'password': '12345'}))
    response_data = response.get_json()
    assert response_data['response']['active'] is True
    assert 'ip' in response_data['response'] and 'csrf_token' in response_data['response']
    with client.session_transaction() as sess:
        assert 'user_id' in sess and 'session_hash' in sess


def test_login_persistent(client):
    response = client.post('/login', data=json.dumps({
        'username': 'lights',
        'password': '12345',
        'persistent': True,
        }))
    response_data = response.get_json()

    assert response_data['response']['persistent'] is True


def test_login_failure(client):
    response = client.post('/login', data=json.dumps({
        'username': 'not_lights', 'password': '54321'}))

    check_json_response(response, 'Invalid credentials.')
    assert response.status_code == 401


@pytest.mark.parametrize(
    'username, password, persistence', [
        (b'{\xbe\xc9\xa9\x15s', b'U\xa5\x9e\xbd\x9b\xb0\xcfL', 'true'),
        (13313, False, True),
        ('lights', '12345', 'False'),
    ])
def test_schema_failure(username, password, persistence):
    with pytest.raises(Invalid):
        login_schema(dict(
            username=username,
            password=password,
            persistent=persistence,
            ))
