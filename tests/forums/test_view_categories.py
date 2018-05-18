import json
import pytest
from conftest import add_permissions, check_json_response


def test_view_categories(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/categories')
    check_json_response(response, {
        'id': 1,
        'name': 'Site',
        'description': 'General site discussion',
        }, list_=True)
    assert response.status_code == 200


def test_add_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.post('/forums/categories', data=json.dumps({
        'name': 'New Forum',
        'description': 'New Description',
        'position': 99,
        }))
    check_json_response(response, {
        'id': 6,
        'name': 'New Forum',
        'description': 'New Description',
        'position': 99
        })


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/forums/categories', 'GET'),
        ('/forums/categories', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
