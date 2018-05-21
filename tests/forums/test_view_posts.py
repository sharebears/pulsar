import json
from datetime import datetime

import mock
import pytest
import pytz

from conftest import add_permissions, check_json_response
from pulsar.forums.models import ForumPost, ForumPostEditHistory


def test_view_post(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/posts/1')
    check_json_response(response, {
        'id': 1,
        'contents': '!site New yeah',
        })
    assert response.status_code == 200


def test_add_post(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts')
    response = authed_client.post('/forums/posts', data=json.dumps({
        'thread_id': 1,
        'contents': 'hahe new forum post',
        }))
    check_json_response(response, {
        'id': 9,
        'contents': 'hahe new forum post',
        'thread_id': 1,
        })


def test_add_post_locked(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts')
    response = authed_client.post('/forums/posts', data=json.dumps({
        'thread_id': 3,
        'contents': 'hahe new forum post',
        }))
    check_json_response(response, 'You cannot post in a locked thread.')


def test_add_post_length_limit(app, authed_client, monkeypatch):
    with mock.patch('pulsar.forums.posts.len', lambda _: 200000):
        add_permissions(app, 'view_forums', 'create_forum_posts')
        response = authed_client.post('/forums/posts', data=json.dumps({
            'thread_id': 5,
            'contents': 'hahe new forum post',
            }))
        check_json_response(
            response,
            'Post could not be merged into previous post (must be <256,000 characters combined).')


def test_add_post_double_post(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts')
    response = authed_client.post('/forums/posts', data=json.dumps({
        'thread_id': 5,
        'contents': 'hahe new forum post',
        }))
    check_json_response(response, {
        'id': 3,
        'contents': 'How do we increase donations?\n\n\nhahe new forum post',
        'thread_id': 5,
        })


def test_add_post_double_post_and_locked_override(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts', 'forum_double_post',
                    'forums_post_in_locked_threads')
    response = authed_client.post('/forums/posts', data=json.dumps({
        'thread_id': 3,
        'contents': 'hahe new forum post',
        }))
    check_json_response(response, {
        'id': 9,
        'contents': 'hahe new forum post',
        'thread_id': 3,
        })


def test_add_post_nonexistent_thread(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts')
    response = authed_client.post('/forums/posts', data=json.dumps({
        'thread_id': 100,
        'contents': 'New Post',
        }))
    check_json_response(response, 'ForumThread 100 does not exist.')


def test_edit_post_self(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts')
    response = authed_client.put('/forums/posts/8', data=json.dumps({
        'contents': 'New site, yeah!',
        }))
    check_json_response(response, {
        'id': 8,
        'contents': 'New site, yeah!',
        })
    post = ForumPost.from_id(8)
    assert post.id == 8
    assert post.contents == 'New site, yeah!'
    post_edits = ForumPostEditHistory.from_post(8)
    assert len(post_edits) == 1
    assert (datetime.utcnow().replace(tzinfo=pytz.utc) - post_edits[0].time).total_seconds() < 60
    assert post_edits[0].contents == 'I dont understand this post'
    assert post_edits[0].editor_id == 1
    assert post_edits[0].post_id == 8


def test_edit_post_other_and_history(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts', 'modify_forum_posts')
    response = authed_client.put('/forums/posts/7', data=json.dumps({
        'contents': 'snipped',
        }))
    check_json_response(response, {
        'id': 7,
        'contents': 'snipped',
        })
    post = ForumPost.from_id(7)
    assert post.contents == 'snipped'
    post_edits = ForumPostEditHistory.from_post(7)
    assert len(post_edits) == 1
    assert ((datetime.utcnow().replace(tzinfo=pytz.utc)
             - post_edits[0].time).total_seconds() < 60)
    assert post_edits[0].contents == "Dont delete this!"
    assert post_edits[0].editor_id == 2
    assert post_edits[0].post_id == 7


def test_edit_post_other_no_contents_mod_advanced_locked_override(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts', 'modify_forum_posts')
    response = authed_client.put('/forums/posts/2', data=json.dumps({
        'sticky': True,
        }))
    check_json_response(response, {
        'id': 2,
        'contents': 'Why the fuck is Gazelle in PHP?!',
        'sticky': True,
        })
    post = ForumPost.from_id(2)
    assert post.sticky is True
    post_edits = ForumPostEditHistory.from_post(2)
    assert len(post_edits) == 1


def test_edit_post_locked_thread(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts')
    response = authed_client.put('/forums/posts/2', data=json.dumps({
        'sticky': True,
        }))
    check_json_response(response, 'You cannot modify posts in a locked thread.')


def test_edit_post_deleted_thread(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts', 'modify_forum_posts')
    response = authed_client.put('/forums/posts/1', data=json.dumps({
        'sticky': True,
        }))
    check_json_response(response, 'ForumPost 1 does not exist.')


def test_edit_post_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'create_forum_posts', 'modify_forum_posts')
    response = authed_client.put('/forums/posts/100', data=json.dumps({
        'sticky': True,
        }))
    check_json_response(response, 'ForumPost 100 does not exist.')


def test_delete_post(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_posts_advanced')
    response = authed_client.delete('/forums/posts/1')
    check_json_response(response, 'ForumPost 1 has been deleted.')
    post = ForumPost.from_id(1, include_dead=True)
    assert post.deleted


def test_delete_post_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_posts_advanced')
    response = authed_client.delete('/forums/posts/100')
    check_json_response(response, 'ForumPost 100 does not exist.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/forums/posts/1', 'GET'),
        ('/forums/posts/1', 'DELETE'),
        ('/forums/posts/1', 'PUT'),
        ('/forums/posts', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
