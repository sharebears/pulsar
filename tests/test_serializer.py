from datetime import datetime

import pytest
import pytz

from conftest import add_permissions
from pulsar import NewJSONEncoder, cache
from pulsar.models import User


def test_serialize_user_attributes(app, authed_client):
    user = User.from_id(2)
    data = NewJSONEncoder()._to_dict(user)
    assert 'id' in data
    assert 'email' not in data
    assert 'inviter' not in data

    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user)
    assert 'id' in data
    assert 'email' in data
    assert 'inviter' not in data

    add_permissions(app, 'moderate_users')
    cache.delete(user.__cache_key_permissions__.format(id=2))

    user = User.from_id(2)
    data = NewJSONEncoder()._to_dict(user)
    assert 'id' in data
    assert 'email' in data
    assert 'inviter' in data


def test_to_dict_plain(app, authed_client):
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
    assert dict_ == NewJSONEncoder()._objects_to_dict(dict_)


def test_failed_serialization_default():
    with pytest.raises(TypeError):
        NewJSONEncoder().default('a string')


def test_serialization_of_datetimes():
    time = datetime.utcnow().replace(tzinfo=pytz.utc)
    posix_time = int(time.timestamp())
    assert posix_time > 1500000000
    assert posix_time == NewJSONEncoder().default(time)


def test_serialization_of_datetimes_models(app, authed_client):
    time = datetime.utcnow().replace(tzinfo=pytz.utc)
    posix_time = int(time.timestamp())
    data = {
        'key': time,
        'key2': User.from_id(1),
        'key3': [time, None, time],
    }

    response = NewJSONEncoder()._objects_to_dict(data)
    assert response['key'] == posix_time
    assert 'id' in response['key2']
    assert 'username' in response['key2'] and response['key2']['username'] == 'lights'
    assert len(response['key3']) == 2
    assert all(k == posix_time for k in response['key3'])
