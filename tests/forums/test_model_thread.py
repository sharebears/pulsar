import pytest

from conftest import add_permissions, check_dictionary
from pulsar import APIException, NewJSONEncoder, _403Exception, cache, db
from pulsar.forums.models import (ForumLastViewedPost, ForumPost, ForumThread,
                                  ForumThreadSubscription)


def test_thread_from_pk(app, authed_client):
    thread = ForumThread.from_pk(1)
    assert thread.id == 1
    assert thread.topic == 'New Site'


def test_thread_from_pk_deleted(app, authed_client):
    assert ForumThread.from_pk(2) is None


def test_thread_no_permissions(app, authed_client):
    db.session.execute("DELETE FROM forums_permissions")
    with pytest.raises(_403Exception):
        ForumThread.from_pk(1)


def test_thread_can_access_implicit_forum(app, authed_client):
    db.session.execute("DELETE FROM forums_permissions")
    add_permissions(app, 'forums_forums_permission_1')
    thread = ForumThread.from_pk(1)
    assert thread.id == 1
    assert thread.topic == 'New Site'


def test_thread_can_access_explicit_disallow(app, authed_client):
    db.session.execute("DELETE FROM forums_permissions")
    add_permissions(app, 'forums_forums_permission_1')
    db.session.execute("""INSERT INTO forums_permissions (user_id, permission, granted)
                       VALUES (1, 'forums_threads_permission_1', 'f')""")
    with pytest.raises(_403Exception):
        ForumThread.from_pk(1)


def test_thread_cache(app, authed_client):
    thread = ForumThread.from_pk(1)
    cache.cache_model(thread, timeout=60)
    thread = ForumThread.from_pk(1)
    assert thread.id == 1
    assert thread.topic == 'New Site'
    assert cache.ttl(thread.cache_key) < 61


def test_thread_get_from_forum(app, authed_client):
    threads = ForumThread.from_forum(1, page=1, limit=50)
    assert len(threads) == 1

    for thread in threads:
        if thread.topic == 'New Site' and thread.id == 1:
            break
    else:
        raise AssertionError('A real thread not called')


def test_thread_get_from_forum_no_perms(app, authed_client):
    db.session.execute("DELETE FROM forums_permissions")
    threads = ForumThread.from_forum(1, page=1, limit=50)
    assert len(threads) == 0


def test_thread_get_from_forum_cached(app, authed_client):
    cache.set(ForumThread.__cache_key_of_forum__.format(id=2), [1, 5], timeout=60)
    ForumThread.from_pk(1); ForumThread.from_pk(5)  # noqa cache these
    threads = ForumThread.from_forum(2, page=1, limit=50)
    assert len(threads) == 2

    for thread in threads:
        if thread.topic == 'Donations?' and thread.id == 5:
            break
    else:
        raise AssertionError('A real thread not called')


def test_new_thread(app, authed_client):
    thread = ForumThread.new(
        topic='NewForumThread',
        forum_id=2,
        poster_id=1)
    assert thread.topic == 'NewForumThread'
    assert thread.forum_id == 2
    assert thread.poster_id == 1
    assert ForumThread.from_cache(thread.cache_key).id == thread.id == 6


@pytest.mark.parametrize(
    'forum_id, poster_id', [
        (10, 1), (3, 1), (1, 6)])
def test_new_thread_failure(app, authed_client, forum_id, poster_id):
    with pytest.raises(APIException):
        ForumThread.new(
            topic='NewForumThread',
            forum_id=forum_id,
            poster_id=poster_id)


@pytest.mark.parametrize(
    'thread_id, count', [
        (1, 0), (5, 1)])
def test_thread_post_count(app, authed_client, thread_id, count):
    assert ForumThread.from_pk(thread_id).post_count == count


def test_thread_post_count_cached(app, authed_client):
    cache.set(ForumThread.__cache_key_post_count__.format(id=1), 100)
    assert ForumThread.from_pk(1).post_count == 100


def test_thread_posts(app, authed_client):
    thread = ForumThread.from_pk(2, include_dead=True)
    posts = thread.posts
    assert len(posts) == 2
    assert any(p.contents == '!site New yeah' for p in posts)


def test_thread_threads_setter(app, authed_client):
    thread = ForumThread.from_pk(2, include_dead=True)
    thread.set_posts(page=1, limit=1)
    posts = thread.posts
    assert len(posts) == 1
    assert posts[0].contents == '!site New yeah'


def test_thread_posts_with_deleted(app, authed_client):
    thread = ForumThread.from_pk(5)
    posts = thread.posts
    assert len(posts) == 1
    assert posts[0].contents == 'How do we increase donations?'


def test_thread_last_post(app, authed_client):
    thread = ForumThread.from_pk(2, include_dead=True)
    post = thread.last_post
    assert post.contents == 'Delete this'


def test_thread_last_post_empty(app, authed_client):
    thread = ForumThread.from_pk(1, include_dead=True)
    assert thread.last_post is None


def test_thread_last_post_from_cache(app, authed_client):
    cache.set(ForumThread.__cache_key_last_post__.format(id=2), 2)
    thread = ForumThread.from_pk(2, include_dead=True)
    post = thread.last_post
    assert post.contents == 'Why the fuck is Gazelle in PHP?!'


def test_thread_last_post_already_cached(app, authed_client):
    thread = ForumThread.from_pk(2, include_dead=True)
    post = ForumPost.from_pk(6)
    cache.cache_model(post, timeout=60)
    post = thread.last_post
    assert post.contents == 'Delete this'
    assert cache.ttl(post.cache_key) < 61


def test_thread_last_viewed_post_none(app, authed_client):
    thread = ForumThread.from_pk(1)
    assert thread.last_viewed_post is None
    assert not cache.get(
        ForumLastViewedPost.__cache_key__.format(thread_id=1, user_id=1))


def test_thread_last_viewed_post(app, authed_client):
    thread = ForumThread.from_pk(3)
    last_post = thread.last_viewed_post
    assert last_post.id == 2
    assert last_post.thread_id == 3
    assert 2 == cache.get(ForumLastViewedPost.__cache_key__.format(
        thread_id=3, user_id=1))


def test_thread_last_viewed_post_cached(app, authed_client):
    cache.set(ForumLastViewedPost.__cache_key__.format(
        thread_id=1, user_id=1), 2)
    thread = ForumThread.from_pk(1)
    last_post = thread.last_viewed_post
    assert last_post.id == 2
    assert last_post.thread_id == 3
    assert 2 == cache.get(ForumLastViewedPost.__cache_key__.format(
        thread_id=1, user_id=1))


def test_thread_last_viewed_post_deleted(app, authed_client):
    thread = ForumThread.from_pk(5)
    last_post = thread.last_viewed_post
    assert last_post.id == 3
    assert last_post.thread_id == 5
    assert 3 == cache.get(ForumLastViewedPost.__cache_key__.format(
        thread_id=5, user_id=1))


def test_thread_last_viewed_none_available(app, authed_client):
    db.session.execute("DELETE FROM forums_posts WHERE id > 5")
    thread = ForumThread.from_pk(4)
    assert thread.last_viewed_post is None


def test_thread_subscriptions(app, authed_client):
    threads = ForumThread.from_subscribed_user(1)
    assert all(t.id in {1, 3, 4} for t in threads)
    assert {1, 3, 4} == set(
        cache.get(ForumThreadSubscription.__cache_key_of_users__.format(user_id=1)))


def test_thread_subscriptions_active(app, authed_client):
    threads = ForumThread.new_subscriptions(1)
    assert {1, 4} == set(t.id for t in threads)
    assert {1, 4} == set(
        cache.get(ForumThreadSubscription.__cache_key_active__.format(user_id=1)))


def test_user_ids_from_thread_subscription(app, authed_client):
    assert [1] == ForumThreadSubscription.user_ids_from_thread(2)
    assert {1, 2} == set(ForumThreadSubscription.user_ids_from_thread(4))


def test_forum_thread_subscriptions_cache_keys_thread_id(app, authed_client):
    user_ids = ForumThreadSubscription.user_ids_from_thread(4)  # noqa
    cache.set(ForumThreadSubscription.__cache_key_of_users__.format(user_id=1), [14, 23])
    cache.set(ForumThreadSubscription.__cache_key_active__.format(user_id=1), [12, 28])
    cache.set(ForumThreadSubscription.__cache_key_users__.format(thread_id=4), [3, 4, 5])
    assert 3 == len(cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=4)))
    ForumThreadSubscription.clear_cache_keys(thread_id=4)
    assert 2 == len(cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=4)))
    assert not cache.has(ForumThreadSubscription.__cache_key_active__.format(user_id=1))
    assert [14, 23] == cache.get(ForumThreadSubscription.__cache_key_of_users__.format(user_id=1))


def test_forum_thread_subscriptions_cache_keys_user_ids(app, authed_client):
    user_ids = ForumThreadSubscription.user_ids_from_thread(4)  # noqa
    cache.set(ForumThreadSubscription.__cache_key_of_users__.format(user_id=1), [14, 23])
    cache.set(ForumThreadSubscription.__cache_key_active__.format(user_id=1), [12, 28])
    cache.set(ForumThreadSubscription.__cache_key_users__.format(thread_id=4), [3, 4, 5])
    assert 3 == len(cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=4)))
    ForumThreadSubscription.clear_cache_keys(user_ids=[1, 2])
    assert 3 == len(cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=4)))
    assert not cache.has(ForumThreadSubscription.__cache_key_active__.format(user_id=1))
    assert not cache.get(ForumThreadSubscription.__cache_key_of_users__.format(user_id=1))


def test_serialize_no_perms(app, authed_client):
    category = ForumThread.from_pk(3)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 3,
        'topic': 'Using PHP',
        'locked': True,
        'sticky': True,
        'post_count': 1,
        })
    assert 'forum' in data and data['forum']['id'] == 2
    assert 'poster' in data and data['poster']['id'] == 2
    assert 'last_post' in data and data['last_post']['id'] == 2
    assert 'last_viewed_post' in data and data['last_viewed_post']['id'] == 2
    assert ('posts' in data
            and len(data['posts']) == 1
            and data['posts'][0]['id'] == 2)
    assert 'created_time' in data and isinstance(data['created_time'], int)
    assert len(data) == 11


def test_serialize_very_detailed(app, authed_client):
    add_permissions(app, 'modify_forum_threads_advanced')
    category = ForumThread.from_pk(3)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 3,
        'topic': 'Using PHP',
        'locked': True,
        'sticky': True,
        'deleted': False,
        'post_count': 1,
        })
    assert 'forum' in data and data['forum']['id'] == 2
    assert 'poster' in data and data['poster']['id'] == 2
    assert 'last_post' in data and data['last_post']['id'] == 2
    assert 'last_viewed_post' in data and data['last_viewed_post']['id'] == 2
    assert ('posts' in data
            and len(data['posts']) == 1
            and data['posts'][0]['id'] == 2)
    assert 'created_time' in data and isinstance(data['created_time'], int)
    assert len(data) == 12


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'modify_forum_threads_advanced')
    category = ForumThread.from_pk(3)
    data = NewJSONEncoder()._to_dict(category, nested=True)
    check_dictionary(data, {
        'id': 3,
        'topic': 'Using PHP',
        'locked': True,
        'sticky': True,
        'deleted': False,
        'post_count': 1,
        })
    assert 'poster' in data and data['poster']['id'] == 2
    assert 'last_post' in data and data['last_post']['id'] == 2
    assert 'last_viewed_post' in data and data['last_viewed_post']['id'] == 2
    assert 'created_time' in data and isinstance(data['created_time'], int)
    assert len(data) == 10
