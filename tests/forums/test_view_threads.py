import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar.forums.models import ForumThread, ForumPost


def test_view_thread(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/threads/1')
    check_json_response(response, {
        'id': 1,
        'topic': 'New Site',
        })
    assert response.status_code == 200


def test_add_thread(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_threads')
    response = authed_client.post('/forums/threads', data=json.dumps({
        'topic': 'New Thread',
        'forum_id': 1,
        }))
    check_json_response(response, {
        'id': 6,
        'topic': 'New Thread',
        })
    assert response.get_json()['response']['forum']['id'] == 1


def test_add_thread_nonexistent_category(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_threads')
    response = authed_client.post('/forums/threads', data=json.dumps({
        'topic': 'New Forum',
        'forum_id': 100,
        }))
    check_json_response(response, 'Invalid Forum ID.')


def test_edit_thread(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads')
    response = authed_client.put('/forums/threads/1', data=json.dumps({
        'topic': 'Bite',
        'forum_id': 4,
        'locked': True,
        }))
    check_json_response(response, {
        'id': 1,
        'topic': 'Bite',
        'locked': True,
        'sticky': False,
        })
    assert response.get_json()['response']['forum']['id'] == 4
    thread = ForumThread.from_id(1)
    assert thread.id == 1
    assert thread.topic == 'Bite'
    assert thread.locked is True
    assert thread.sticky is False


def test_edit_thread_skips(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads')
    response = authed_client.put('/forums/threads/1', data=json.dumps({
        'sticky': True,
        }))
    check_json_response(response, {
        'id': 1,
        'topic': 'New Site',
        'locked': False,
        'sticky': True,
        })
    thread = ForumThread.from_id(1)
    assert thread.sticky is True


def test_edit_thread_bad_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads')
    response = authed_client.put('/forums/threads/1', data=json.dumps({
        'forum_id': 100,
        }))
    check_json_response(response, 'Invalid Forum ID.')


def test_edit_thread_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads')
    response = authed_client.put('/forums/threads/100', data=json.dumps({
        'locked': True,
        }))
    check_json_response(response, 'Forum thread 100 does not exist.')


def test_delete_thread(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads_advanced')
    post = ForumPost.from_id(3)  # Cache - post isn't deleted, belongs to thread
    response = authed_client.delete('/forums/threads/5')
    check_json_response(response, 'Forum thread 5 (Donations?) has been deleted.')
    thread = ForumThread.from_id(5, include_dead=True)
    assert thread.deleted
    post = ForumPost.from_id(3, include_dead=True)
    assert post.deleted


def test_delete_thread_no_posts(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads_advanced')
    response = authed_client.delete('/forums/threads/1')
    check_json_response(response, 'Forum thread 1 (New Site) has been deleted.')
    thread = ForumThread.from_id(1, include_dead=True)
    assert thread.deleted


def test_delete_thread_no_permissions(app, authed_client):
    add_permissions(app, 'view_threads', 'modify_forum_threads')
    response = authed_client.delete('/forums/threads/5')
    check_json_response(response, 'You do not have permission to access this resource.')


def test_delete_thread_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads_advanced')
    response = authed_client.delete('/forums/threads/100')
    check_json_response(response, 'Forum thread 100 does not exist.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/forums/threads/1', 'GET'),
        ('/forums/threads/1', 'DELETE'),
        ('/forums/threads/1', 'PUT'),
        ('/forums/threads', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
