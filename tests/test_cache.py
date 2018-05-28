import flask

from conftest import add_permissions
from pulsar import cache, db
from pulsar.users.models import User


def test_get_from_cache(app, authed_client):
    """Test that cache values are used instead of querying a user."""
    add_permissions(app, 'view_users')
    user = User.from_pk(1)
    data = {}
    for attr in user.__table__.columns.keys():
        data[attr] = getattr(user, attr, None)
    data['username'] = 'fakeshit'
    cache.set(user.cache_key, data)
    user = User.from_pk(1)
    assert user.username == 'fakeshit'


def test_cache_model(app, authed_client):
    """Test that caching a model works."""
    user = User.from_pk(1)
    cache.cache_model(user, timeout=60)
    user_data = cache.get('users_1')
    assert user_data['id'] == 1
    assert user_data['username'] == 'lights'
    assert user_data['enabled'] is True
    assert user_data['inviter_id'] is None


def test_cache_model_when_none(app, client, monkeypatch):
    """Assert caching a None object returns None."""
    assert cache.cache_model(None, timeout=60) is None


def test_from_cache(app, authed_client):
    """Get a user from the cache."""
    user = User.from_pk(1)
    cache.cache_model(user, timeout=60)
    user_new = User.from_cache('users_1')
    assert user_new.id == 1
    assert user_new.email == 'lights@puls.ar'
    assert user_new.enabled is True
    assert user_new.inviter_id is None


def test_from_cache_bad(app, client):
    """Receiving bad model data from the cache; delete it."""
    cache.set('users_1', {'id': 2, 'username': 'not-all-the-keys'}, timeout=60)
    assert not User.from_cache('users_1')
    assert not cache.get('users_1')


def test_cache_inc_key_new(app, client):
    """Incrementing a nonexistent key should create it."""
    value = cache.inc('test-inc-key', 2, timeout=60)
    time_left = cache.ttl('test-inc-key')
    assert value == 2
    assert time_left < 61


def test_cache_inc_key_already_exists(app, client):
    """Incrementing an already-existing key just increments it."""
    assert cache.set('test-inc-key', 3, timeout=15)
    value = cache.inc('test-inc-key', 4, timeout=80)
    time_left = cache.ttl('test-inc-key')
    assert value == 7
    assert time_left > 13 and time_left < 16


def test_cache_autoclear_dirty_and_deleted(app, client):
    """The cache autoclears dirty models upon commit."""
    user = User.from_pk(1)
    user_2 = User.from_pk(3)
    user.set_password('testing')
    db.session.delete(user_2)
    assert cache.has('users_1')
    assert cache.has('users_3')
    db.session.commit()
    assert not cache.has('users_1')
    assert not cache.has('users_3')
    assert not User.from_pk(3)


def test_cache_doesnt_autoclear_dirty_and_deleted_(app, client, monkeypatch):
    """The cache does not autoclear dirty models upon commit if they do not have cache keys."""
    user = User.from_pk(1)
    monkeypatch.setattr('pulsar.users.models.User.__cache_key__', None)
    user.set_password('testing')
    assert cache.has('users_1')
    db.session.commit()
    assert cache.has('users_1')


def test_cache_set_key_bad(app, client, monkeypatch):
    """A bad key should not be added to the DB."""
    monkeypatch.setattr('pulsar.cache._client.setex', lambda *a, **k: False)
    with app.test_request_context('/test'):
        cache.set('blah', 2, timeout=60)
        assert 'blah' not in flask.g.cache_keys['set']


def test_cache_has_key(app, client):
    """The `has_key` function should return True/False based on key existence."""
    cache.set('test_1', 1)
    assert cache.has('test_1')
    assert not cache.has('test_2')


def test_cache_get_dict(app, client):
    cache.set('key_1', 1)
    cache.set('key_2', 2)
    data = cache.get_dict(*('keY_1', 'kEy_2', 'key_3'))
    assert data == {
        'key_1': 1,
        'key_2': 2,
        'key_3': None,
    }
    with app.test_request_context('/test'):
        assert 'key_1' in flask.g.cache_keys['get_dict']
        assert 'key_2' in flask.g.cache_keys['get_dict']
        assert 'key_3' in flask.g.cache_keys['get_dict']


def test_cache_get_dict_order(app, client):
    cache.set('key_4', 4)
    cache.set('key_3', 3)
    cache.set('key_5', 5)
    cache.set('key_1', 1)
    cache.set('key_2', 2)
    data = cache.get_dict(*('key_2', 'key_1', 'key_3', 'key_4', 'key_5'))
    assert list(data.keys()) == ['key_2', 'key_1', 'key_3', 'key_4', 'key_5']


def test_cache_set_many(app, client):
    cache.set_many({'key_1': 1, 'Key_2': 3})
    assert cache.get('key_1') == 1
    assert cache.get('key_2') == 3
    with app.test_request_context('/test'):
        assert 'key_1' in flask.g.cache_keys['set_many']
        assert 'key_2' in flask.g.cache_keys['set_many']


def test_cache_delete_many(app, client):
    cache.set('key_1', 1)
    cache.set('key_2', 2)
    assert cache.delete_many('key_1', 'key_2', 'key_3')
    with app.test_request_context('/test'):
        assert 'key_1' in flask.g.cache_keys['delete_many']
        assert 'key_2' in flask.g.cache_keys['delete_many']
        assert 'key_3' in flask.g.cache_keys['delete_many']


def test_cache_sets_globals(app, authed_client):
    """Modifying cache values should add them to the global variables."""
    @app.route('/test_route')
    def test_route():
        cache.set('key3', 1)
        cache.inc('key1')
        cache.get('key2')
        cache.ttl('key2')
        cache.ttl('key3')
        cache.get('key3')
        cache.delete('key3')
        cache.delete('key4')

        assert cache.has('key1')
        assert flask.g.cache_keys['inc'] == {'key1'}
        assert flask.g.cache_keys['get'] == {'key3'}
        assert flask.g.cache_keys['set'] == {'key3'}
        assert flask.g.cache_keys['delete'] == {'key3'}
        assert flask.g.cache_keys['ttl'] == {'key3'}
        assert flask.g.cache_keys['has'] == {'key1'}
        return flask.jsonify('complete')

    authed_client.get('/test_route')
