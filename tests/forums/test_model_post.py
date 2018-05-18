import pytest

from conftest import check_dictionary, add_permissions
from pulsar import cache, NewJSONEncoder
from pulsar.models import ForumPost, ForumPostEditHistory


def test_post_from_id_deleted(app, authed_client):
    assert ForumPost.from_id(4) is None


def test_post_cache(app, authed_client):
    post = ForumPost.from_id(1)
    cache.cache_model(post, timeout=60)
    post = ForumPost.from_id(1)
    assert post.id == 1
    assert post.contents == '!site New yeah'
    assert cache.ttl(post.cache_key) < 61


def test_post_get_from_thread(app, authed_client):
    posts = ForumPost.from_thread(5, page=1, limit=50)
    assert len(posts) == 1

    for post in posts:
        if post.contents == 'How do we increase donations?' and post.id == 3:
            break
    else:
        raise AssertionError('A real post not called')


def test_post_get_from_thread_cached(app, authed_client):
    cache.set(ForumPost.__cache_key_of_thread__.format(id=2), ['1', '6'], timeout=60)
    posts = ForumPost.from_thread(2, page=1, limit=50)
    assert len(posts) == 2

    for post in posts:
        if post.contents == 'Delete this' and post.id == 6:
            break
    else:
        raise AssertionError('A real post not called')


def test_new_post(app, authed_client):
    post = ForumPost.new(
        thread_id=3,
        poster_id=1,
        contents='NewForumPost')
    assert post.thread_id == 3
    assert post.poster_id == 1
    assert post.contents == 'NewForumPost'
    assert ForumPost.from_cache(post.cache_key).id == post.id == 7


@pytest.mark.parametrize(
    'thread_id, poster_id', [
        (10, 1), (2, 1), (1, 6)])
def test_new_post_failure(app, authed_client, thread_id, poster_id):
    assert ForumPost.new(
        thread_id=thread_id,
        poster_id=poster_id,
        contents='NewForumPost'
        ) is None


def test_post_edit_history_from_id(app, authed_client):
    history = ForumPostEditHistory.from_id(2)
    assert history.post_id == 2
    assert history.id == 2
    assert history.contents == 'Why the shit is Pizzelle in GPG?'


def test_post_edit_history_from_id_cached(app, authed_client):
    history = ForumPostEditHistory.from_id(2)
    cache.cache_model(history, timeout=60)
    history = ForumPostEditHistory.from_id(2)
    assert history.post_id == 2
    assert cache.ttl(history.cache_key) < 61


def test_post_edit_history_from_post(app, authed_client):
    history = ForumPostEditHistory.from_post(3)
    assert len(history) == 2
    assert any(h.contents == 'New typo' for h in history)


def test_post_edit_history_from_cache(app, authed_client):
    cache.set(ForumPostEditHistory.__cache_key_of_post__.format(id=3), [1])
    history = ForumPostEditHistory.from_post(3)
    assert len(history) == 1
    assert any(h.contents == 'Why the fcuk is Gazelle in HPH?' for h in history)


def test_serialize_no_perms(app, client):
    category = ForumPost.from_id(1)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 1,
        'thread_id': 2,
        'contents': '!site New yeah',
        'sticky': True,
        'editor': None,
        })
    assert 'poster' in data and data['poster']['id'] == 1
    assert 'time' in data and isinstance(data['time'], int)
    assert len(data) == 7


def test_serialize_very_detailed(app, authed_client):
    add_permissions(app, 'modify_forum_posts_advanced')
    category = ForumPost.from_id(1)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 1,
        'thread_id': 2,
        'contents': '!site New yeah',
        'sticky': True,
        'editor': None,
        'deleted': False,
        })
    assert 'poster' in data and data['poster']['id'] == 1
    assert 'time' in data and isinstance(data['time'], int)
    assert ('edit_history' in data
            and data['edit_history'][0]['id'] == 1
            and len(data['edit_history']) == 1)
    assert len(data) == 9


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'modify_forum_posts_advanced')
    category = ForumPost.from_id(1)
    data = NewJSONEncoder()._to_dict(category, nested=True)
    check_dictionary(data, {
        'id': 1,
        'contents': '!site New yeah',
        'sticky': True,
        'editor': None,
        'deleted': False,
        })
    assert 'poster' in data and data['poster']['id'] == 1
    assert 'time' in data and isinstance(data['time'], int)
    assert ('edit_history' in data
            and data['edit_history'][0]['id'] == 1
            and len(data['edit_history']) == 1)
    assert len(data) == 8
