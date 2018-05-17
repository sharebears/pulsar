import pytest

from pulsar import cache
from pulsar.models import ForumPost, ForumThread


def test_thread_from_id(app, authed_client):
    thread = ForumThread.from_id(1)
    assert thread.id == 1
    assert thread.topic == 'New Site'


def test_thread_from_id_deleted(app, authed_client):
    assert ForumThread.from_id(2) is None


def test_thread_cache(app, authed_client):
    thread = ForumThread.from_id(1)
    cache.cache_model(thread, timeout=60)
    thread = ForumThread.from_id(1)
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


def test_thread_get_from_forum_cached(app, authed_client):
    cache.set(ForumThread.__cache_key_of_forum__.format(id=2), ['1', '5'], timeout=60)
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
    assert ForumThread.new(
        topic='NewForumThread',
        forum_id=forum_id,
        poster_id=poster_id) is None


@pytest.mark.parametrize(
    'thread_id, count', [
        (1, 0), (5, 1)])
def test_thread_post_count(app, authed_client, thread_id, count):
    assert ForumThread.from_id(thread_id).post_count == count


def test_thread_post_count_cached(app, authed_client):
    cache.set(ForumThread.__cache_key_post_count__.format(id=1), 100)
    assert ForumThread.from_id(1).post_count == 100


def test_thread_posts(app, authed_client):
    thread = ForumThread.from_id(2, include_dead=True)
    posts = thread.posts
    assert len(posts) == 2
    assert any(p.contents == '!site New yeah' for p in posts)


def test_thread_threads_setter(app, authed_client):
    thread = ForumThread.from_id(2, include_dead=True)
    thread.set_posts(page=1, limit=1)
    posts = thread.posts
    assert len(posts) == 1
    assert posts[0].contents == '!site New yeah'


def test_thread_posts_with_deleted(app, authed_client):
    thread = ForumThread.from_id(5)
    posts = thread.posts
    assert len(posts) == 1
    assert posts[0].contents == 'How do we increase donations?'


def test_thread_last_post(app, authed_client):
    thread = ForumThread.from_id(2, include_dead=True)
    post = thread.last_post
    assert post.contents == 'Delete this'


def test_thread_last_post_empty(app, authed_client):
    thread = ForumThread.from_id(1, include_dead=True)
    assert thread.last_post is None


def test_thread_last_post_from_cache(app, authed_client):
    cache.set(ForumThread.__cache_key_last_post__.format(id=2), 2)
    thread = ForumThread.from_id(2, include_dead=True)
    post = thread.last_post
    assert post.contents == 'Why the fuck is Gazelle in PHP?!'


def test_thread_last_post_already_cached(app, authed_client):
    thread = ForumThread.from_id(2, include_dead=True)
    post = ForumPost.from_id(6)
    cache.cache_model(post, timeout=60)
    post = thread.last_post
    assert post.contents == 'Delete this'
    assert cache.ttl(post.cache_key) < 61
