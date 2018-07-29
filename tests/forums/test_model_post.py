import pytest

from conftest import add_permissions, check_dictionary
from pulsar import APIException, NewJSONEncoder, cache
from pulsar.forums.models import ForumPost, ForumPostEditHistory


def test_post_from_pk_deleted(app, authed_client):
    assert ForumPost.from_pk(4) is None


def test_post_cache(app, authed_client):
    post = ForumPost.from_pk(1)
    cache.cache_model(post, timeout=60)
    post = ForumPost.from_pk(1)
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
    ForumPost.from_pk(1); ForumPost.from_pk(6)  # noqa cache this
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
    assert ForumPost.from_cache(post.cache_key).id == post.id == 9


@pytest.mark.parametrize(
    'thread_id, poster_id', [
        (10, 1), (2, 1), (1, 6)])
def test_new_post_failure(app, authed_client, thread_id, poster_id):
    with pytest.raises(APIException):
        assert ForumPost.new(
            thread_id=thread_id,
            poster_id=poster_id,
            contents='NewForumPost')


def test_post_edit_history_from_pk(app, authed_client):
    history = ForumPostEditHistory.from_pk(2)
    assert history.post_id == 2
    assert history.id == 2
    assert history.contents == 'Why the shit is Pizzelle in GPG?'


def test_post_edit_history_from_pk_cached(app, authed_client):
    history = ForumPostEditHistory.from_pk(2)
    cache.cache_model(history, timeout=60)
    history = ForumPostEditHistory.from_pk(2)
    assert history.post_id == 2
    assert cache.ttl(history.cache_key) < 61


def test_post_edit_history_from_post(app, authed_client):
    history = ForumPostEditHistory.from_post(3)
    assert len(history) == 2
    assert any(h.contents == 'New typo' for h in history)


def test_post_edit_history_from_cache(app, authed_client):
    cache.set(ForumPostEditHistory.__cache_key_of_post__.format(id=3), [1])
    ForumPostEditHistory.from_pk(1)  # cache this
    history = ForumPostEditHistory.from_post(3)
    assert len(history) == 1
    assert any(h.contents == 'Why the fcuk is Gazelle in HPH?' for h in history)


def test_serialize_no_perms(app, authed_client):
    add_permissions(app, 'forums_threads_permission_3')
    post = ForumPost.from_pk(2)
    data = NewJSONEncoder().default(post)
    check_dictionary(data, {
        'id': 2,
        'contents': 'Why the fuck is Gazelle in PHP?!',
        'sticky': True,
        'editor': None,
        })
    assert ('thread' in data
            and data['thread']['id'] == 3
            and len([k for k, v in data['thread'].items() if v]) == 2)
    assert 'poster' in data and data['poster']['id'] == 1
    assert 'time' in data and isinstance(data['time'], int)
    assert 'edited_time' in data


def test_serialize_very_detailed(app, authed_client):
    add_permissions(app, 'modify_forum_posts_advanced')
    post = ForumPost.from_pk(1)
    data = NewJSONEncoder().default(post)
    check_dictionary(data, {
        'id': 1,
        'contents': '!site New yeah',
        'sticky': True,
        'editor': None,
        'deleted': False,
        })
    assert 'thread' in data and data['thread'] is None
    assert 'poster' in data and data['poster']['id'] == 1
    assert 'time' in data and isinstance(data['time'], int)
    assert 'edited_time' in data
    assert ('edit_history' in data
            and data['edit_history'][0]['id'] == 1
            and len(data['edit_history']) == 1)


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'modify_forum_posts_advanced')
    post = ForumPost.from_pk(1)
    data = NewJSONEncoder()._objects_to_dict(post.serialize(nested=True))
    check_dictionary(data, {
        'id': 1,
        'contents': '!site New yeah',
        'sticky': True,
        'editor': None,
        'deleted': False,
        })
    assert 'poster' in data and data['poster']['id'] == 1
    assert 'time' in data and isinstance(data['time'], int)
    assert 'edited_time' in data
    assert ('edit_history' in data
            and data['edit_history'][0]['id'] == 1
            and len(data['edit_history']) == 1)
