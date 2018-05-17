import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar.models import User


def test_int_overflow(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/1/moderate', data=json.dumps({
        'invites': 99999999999999999999999999,
        }))
    check_json_response(response, 'Invalid data: value must be at most 2147483648 (key "invites")')


def test_moderate_user(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/2/moderate', data=json.dumps({
        'email': 'new@ema.il',
        'uploaded': 999,
        'downloaded': 998,
        'invites': 100,
        }))
    check_json_response(response, {
        'id': 2,
        'email': 'new@ema.il',
        'uploaded': 999,
        'downloaded': 998,
        })
    user = User.from_id(2)
    assert user.email == 'new@ema.il'
    assert user.uploaded == 999


def test_moderate_user_incomplete(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/2/moderate', data=json.dumps({
        'password': 'abcdefGHIfJK12#',
        }))
    check_json_response(response, {
        'id': 2,
        'email': 'paffu@puls.ar',
        'downloaded': 0,
        })
    user = User.from_id(2)
    assert user.check_password('abcdefGHIfJK12#')
    assert user.email == 'paffu@puls.ar'


def test_moderate_user_not_found(app, authed_client):
    add_permissions(app, 'moderate_users')
    response = authed_client.put('/users/10/moderate', data=json.dumps({
        'email': 'new@ema.il',
        }))
    check_json_response(response, 'User 10 does not exist.')
    assert response.status_code == 404


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/users/1/moderate', 'PUT'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
