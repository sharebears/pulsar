from datetime import datetime

import pytest
import pytz

from conftest import add_permissions
from pulsar import NewJSONEncoder
from pulsar.models import ForumCategory, User


def test_serialize_model_attributes_unpermissioned(app, authed_client):
    """Make sure default serialization permissions only show the defaults."""
    user = User.from_id(2)
    data = NewJSONEncoder()._to_dict(user)
    assert 'id' in data
    assert 'email' not in data
    assert 'inviter' not in data


def test_serialize_test_self_permissions(app, authed_client):
    """Make sure self-permission works for serialization."""
    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user)
    assert 'id' in data
    assert 'email' in data
    assert 'inviter' not in data


def test_serialize_detailed_permissions_and_nested(app, authed_client):
    """Make sure detailed permissions and nested excludes work."""
    add_permissions(app, 'moderate_users')
    user = User.from_id(2)
    data = NewJSONEncoder()._to_dict(user)
    assert 'id' in data
    assert 'email' in data
    assert 'inviter' in data
    assert 'id' in data['inviter']
    assert 'inviter' not in data['inviter']


def test_serialize_nested_include(app, authed_client):
    """Make sure that nested include permissions work."""
    forums = NewJSONEncoder()._to_dict(ForumCategory.from_id(2))['forums']
    assert len(forums) == 1
    assert forums[0]['name'] == '/_\\'
    assert 'last_updated_thread' in forums[0]
    assert 'category' not in forums[0]


def test_to_dict_plain(app, authed_client):
    """Make sure that _objects_to_dict can iterate over a decently-complex structure."""
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
    """Assert that serialization still fails for invalid inputs."""
    with pytest.raises(TypeError):
        NewJSONEncoder().default('a string')


def test_serialization_of_datetimes():
    """Make sure that datetimes are properly serialized in the new encoder."""
    time = datetime.utcnow().replace(tzinfo=pytz.utc)
    posix_time = int(time.timestamp())
    assert posix_time > 1500000000
    assert posix_time == NewJSONEncoder().default(time)


def test_serialization_of_datetimes_in_models(app, authed_client):
    """Make sure that the JSON Encoder can convert datetimes in models."""
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
