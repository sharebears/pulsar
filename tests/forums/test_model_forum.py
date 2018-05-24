import pytest

from conftest import add_permissions, check_dictionary
from pulsar import APIException, NewJSONEncoder, _403Exception, cache, db
from pulsar.forums.models import Forum, ForumSubscription


def test_forum_from_id(app, authed_client):
    forum = Forum.from_id(1)
    assert forum.name == 'Pulsar'
    assert forum.description == 'Stuff about pulsar'


def test_forum_cache(app, authed_client):
    forum = Forum.from_id(1)
    cache.cache_model(forum, timeout=60)
    forum = Forum.from_id(1)
    assert forum.name == 'Pulsar'
    assert forum.description == 'Stuff about pulsar'
    assert cache.ttl(forum.cache_key) < 61


def test_forum_no_permission(app, authed_client):
    db.session.execute("DELETE FROM forums_permissions")
    with pytest.raises(_403Exception):
        Forum.from_id(1)


def test_forum_get_from_category(app, authed_client):
    forums = Forum.from_category(1)
    assert len([f for f in forums if f]) == 2

    for forum in forums:
        if forum.name == 'Bugs' and forum.id == 2:
            break
    else:
        raise AssertionError('A real forum not called')


def test_forum_get_from_category_no_permissions(app, authed_client):
    db.session.execute("DELETE FROM forums_permissions")
    forums = Forum.from_category(1)
    assert len(forums) == 0


def test_forum_get_from_category_cached(app, authed_client):
    cache.set(Forum.__cache_key_of_category__.format(id=2), ['1', '5'], timeout=60)
    Forum.from_id(1); Forum.from_id(5)  # noqa: cache these
    forums = Forum.from_category(2)
    assert len(forums) == 2

    for forum in forums:
        if forum.name == 'Yacht Funding' and forum.id == 5:
            break
    else:
        raise AssertionError('A real forum not called')


def test_new_forum(app, authed_client):
    forum = Forum.new(
        name='NewForum',
        description=None,
        category_id=2,
        position=100)
    assert forum.name == 'NewForum'
    assert forum.description is None
    assert forum.position == 100
    assert Forum.from_cache(forum.cache_key).id == forum.id == 7


@pytest.mark.parametrize(
    'category_id', [10, 3])
def test_new_forum_failure(app, authed_client, category_id):
    with pytest.raises(APIException):
        Forum.new(
            name='NewForum',
            description=None,
            category_id=category_id,
            position=100)


@pytest.mark.parametrize(
    'forum_id, count', [
        (2, 2), (1, 1), (4, 0)])
def test_forum_thread_count(app, authed_client, forum_id, count):
    assert Forum.from_id(forum_id).thread_count == count


def test_forum_thread_count_from_cache(app, authed_client):
    cache.set(Forum.__cache_key_thread_count__.format(id=2), 40)
    assert Forum.from_id(2).thread_count == 40


def test_forum_last_updated_thread(app, authed_client):
    forum = Forum.from_id(2)
    assert forum.last_updated_thread.id == 3


def test_forum_last_updated_thread_from_cache(app, authed_client):
    cache.set(Forum.__cache_key_last_updated__.format(id=2), 4)
    forum = Forum.from_id(2)
    assert forum.last_updated_thread.id == 4


def test_forum_threads(app, authed_client):
    forum = Forum.from_id(2)
    threads = forum.threads
    assert len(threads) == 2
    assert any(t.topic == 'Using PHP' for t in threads)


def test_forum_threads_setter(app, authed_client):
    forum = Forum.from_id(2)
    forum.set_threads(page=1, limit=1)
    threads = forum.threads
    assert len(threads) == 1
    assert threads[0].topic == 'Using PHP'


def test_forum_threads_with_deleted(app, authed_client):
    forum = Forum.from_id(1)
    threads = forum.threads
    assert len(threads) == 1
    assert threads[0].topic != 'New Site Borked'


def test_forum_subscriptions(app, authed_client):
    db.session.execute("""INSERT INTO forums_forums_subscriptions (user_id, forum_id) VALUES
                       (1, 1), (1, 2), (1, 3)""")
    forums = Forum.from_subscribed_user(1)
    assert len(forums) == 2
    assert all(f.id in {1, 2} for f in forums)
    assert {1, 2} == set(
        cache.get(ForumSubscription.__cache_key__.format(user_id=1)))


def test_serialize_no_perms(app, authed_client):
    category = Forum.from_id(1)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 1,
        'name': 'Pulsar',
        'description': 'Stuff about pulsar',
        'position': 1,
        'thread_count': 1,
        })
    assert 'category' in data and data['category']['id'] == 1
    assert 'threads' in data and len(data['threads']) == 1
    assert len(data) == 7


def test_serialize_very_detailed(app, authed_client):
    add_permissions(app, 'modify_forums')
    category = Forum.from_id(1)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 1,
        'name': 'Pulsar',
        'description': 'Stuff about pulsar',
        'position': 1,
        'thread_count': 1,
        'deleted': False,
        })
    assert 'category' in data and data['category']['id'] == 1
    assert 'threads' in data and len(data['threads']) == 1
    assert len(data) == 8


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'modify_forums')
    category = Forum.from_id(1)
    data = NewJSONEncoder()._to_dict(category, nested=True)
    check_dictionary(data, {
        'id': 1,
        'name': 'Pulsar',
        'description': 'Stuff about pulsar',
        'position': 1,
        'thread_count': 1,
        'deleted': False,
        })
    assert 'last_updated_thread' in data and 'id' in data['last_updated_thread']
    assert len(data) == 7
