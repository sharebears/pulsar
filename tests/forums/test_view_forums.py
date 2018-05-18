import json
import pytest
from conftest import add_permissions, check_json_response
from pulsar.forums.models import Forum, ForumThread


def test_view_forum(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/2')
    check_json_response(response, {
        'id': 2,
        'name': 'Bugs',
        'description': 'Squishy Squash',
        })
    assert response.status_code == 200


def test_add_forum(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.post('/forums', data=json.dumps({
        'name': 'New Forum',
        'category_id': 1,
        'description': 'New Description',
        'position': 99,
        }))
    check_json_response(response, {
        'id': 6,
        'name': 'New Forum',
        'description': 'New Description',
        })


def test_add_forum_nonexistent_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.post('/forums', data=json.dumps({
        'name': 'New Forum',
        'category_id': 100,
        }))
    check_json_response(response, 'Invalid category ID.')


def test_edit_forum(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/1', data=json.dumps({
        'name': 'Bite',
        'description': 'Very New Description',
        'category_id': 4,
        }))
    check_json_response(response, {
        'id': 1,
        'name': 'Bite',
        'description': 'Very New Description',
        })
    assert response.get_json()['response']['category']['id'] == 4
    forum = Forum.from_id(1)
    assert forum.id == 1
    assert forum.name == 'Bite'
    assert forum.description == 'Very New Description'
    assert forum.category_id == 4


def test_edit_forum_skips(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/1', data=json.dumps({
        'position': 0,
        }))
    check_json_response(response, {
        'id': 1,
        'name': 'Pulsar',
        'description': 'Stuff about pulsar',
        'position': 0,
        })
    forum = Forum.from_id(1)
    assert forum.position == 0


def test_edit_forum_bad_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/1', data=json.dumps({
        'category_id': 100,
        }))
    check_json_response(response, 'Invalid category ID.')


def test_delete_forum(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    sub_thread = ForumThread.from_id(5)  # Cache - thread isn't deleted, belongs to category
    response = authed_client.delete('/forums/5')
    check_json_response(response, 'Forum 5 (Yacht Funding) has been deleted.')
    forum = ForumThread.from_id(5, include_dead=True)
    assert forum.deleted
    sub_thread = ForumThread.from_id(5, include_dead=True)
    assert sub_thread.deleted


def test_delete_forum_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.delete('/forums/100')
    check_json_response(response, 'Forum 100 does not exist.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/forums/1', 'GET'),
        ('/forums', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
