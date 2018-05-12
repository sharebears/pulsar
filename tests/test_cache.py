import pytest
from conftest import add_permissions, check_json_response
from pulsar import cache
from pulsar.users.models import User


def test_get_user_cache(app, authed_client, monkeypatch):
    add_permissions(app, 'view_users')
    monkeypatch.setattr('pulsar.users.models.User.query.get', lambda _: None)
    cache.set('users_1', {
        'id': 1,
        'username': 'fakeshit',
        'passhash': 'abcdefg',
        'email': 'lights@puls.ar',
        'enabled': True,
        'locked': False,
        'user_class': 'User',
        'inviter_id': None,
        'invites': 999,
        'uploaded': 9999999,
        'downloaded': 0,
        })

    response = authed_client.get('/users/1')
    check_json_response(response, {
        'id': 1,
        'username': 'fakeshit',
        })
    assert response.status_code == 200


def test_cache_inc_key(app, client):
    value = cache.inc('test-inc-key', 2, timeout=60)
    time_left = cache.ttl('test-inc-key')
    assert value == 2
    assert time_left > 58 and time_left < 61


def test_cache_inc_key_already_exists(app, client):
    assert cache.set('test-inc-key', 3, timeout=15)
    value = cache.inc('test-inc-key', 4)
    time_left = cache.ttl('test-inc-key')
    assert value == 7
    assert time_left > 13 and time_left < 16


def test_cache_model(app, authed_client):
    user = User.from_id(1)
    cache.cache_model(user, timeout=60)
    user_data = cache.get('users_1')
    assert user_data['id'] == 1
    assert user_data['username'] == 'lights'
    assert user_data['enabled'] is True
    assert user_data['inviter_id'] is None


def test_cache_model_when_none(app, client, monkeypatch):
    assert cache.cache_model(None, timeout=60) is None


def test_model_clear_cache(app, authed_client):
    user = User.from_id(1)
    cache.cache_model(user, timeout=60)
    user_data = cache.get('users_1')
    assert user_data['id'] == 1

    user.clear_cache()
    assert not cache.get('users_1')


def test_from_cache(app, authed_client):
    user = User.from_id(1)
    cache.cache_model(user, timeout=60)
    user_new = User.from_cache('users_1')
    assert user_new.id == 1
    assert user_new.email == 'lights@puls.ar'
    assert user_new.enabled is True
    assert user_new.inviter_id is None


def test_from_cache_bad(app, client):
    cache.set('users_1', {'id': 2, 'username': 'not-all-the-keys'}, timeout=60)
    assert not User.from_cache('users_1')
    assert not cache.get('users_1')


def test_serialize_user_attributes(app, authed_client):
    user = User.from_id(2)
    data = user.to_dict()
    assert 'id' in data
    assert 'email' not in data
    assert 'inviter' not in data

    user = User.from_id(1)
    data = user.to_dict()
    assert 'id' in data
    assert 'email' in data
    assert 'inviter' not in data

    add_permissions(app, 'moderate_users')
    cache.delete(user.__cache_key_permissions__.format(id=2))

    user = User.from_id(2)
    data = user.to_dict()
    assert 'id' in data
    assert 'email' in data
    assert 'inviter' in data


def test_to_dict_plain(app, authed_client):
    user = User.from_id(1)  # Instantiation fodder.
    dict_ = {
        'key1': {
            'subkey1': 'subval1',
            'subkey2': 'subval2',
            'subkey3': [
                'subval1',
                'subval2',
                {
                    'subkey1': 'subkey1',
                    'subkey2': 'subkey2',
                    'subkey3': 'subval3',
                },
            ],
        },
        'key2': 123,
    }
    assert dict_ == user._objects_to_dict(dict_)


@pytest.mark.parametrize(
    'data, result', [
        ('not-a-dict', False),
        ({'id': 1, 'username': 'lights'}, False),
     ])
def test_is_valid_data(app, client, data, result):
    assert User._valid_data(data) is result
