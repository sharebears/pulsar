import pytest
from voluptuous import MultipleInvalid
from conftest import add_permissions

from pulsar.auth.api_keys import (
    VIEW_ALL_API_KEYS_SCHEMA,
    CREATE_API_KEY_SCHEMA,
    REVOKE_API_KEY_SCHEMA, )
from pulsar.auth.sessions import (
    VIEW_ALL_SESSIONS_SCHEMA,
    CREATE_SESSION_SCHEMA,
    EXPIRE_SESSION_SCHEMA, )


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_api_keys_schema(input_):
    assert VIEW_ALL_API_KEYS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_api_keys_schema_failure(input_):
    with pytest.raises(MultipleInvalid):
        VIEW_ALL_API_KEYS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'data', [
        {'permissions': ['perm_one', 'perm_two']},
        {'permissions': []},
        {},
    ])
def test_create_api_key_schema(app, authed_client, data):
    add_permissions(app, 'perm_one', 'perm_two')
    assert data == CREATE_API_KEY_SCHEMA(data)


@pytest.mark.parametrize(
    'data', [
        {'permissions': ['perm_one', 'perm_two']},
        {'permissions': None},
    ])
def test_create_api_key_schema_failure(authed_client, data):
    with pytest.raises(MultipleInvalid):
        CREATE_API_KEY_SCHEMA(data)


@pytest.mark.parametrize(
    'data', [{'id': 'abcdefghij'}, {'id': '13082AFjaw'},
             {'id': '\x02\xb0\xc0AZ\xf2\x99\x22\x8b\xdc'}])
def test_revoke_api_key_schema(data):
    assert data == REVOKE_API_KEY_SCHEMA(data)


@pytest.mark.parametrize(
    'data', [{'id': 1240312412}, {'id': None}])
def test_revoke_api_key_schema_failure(data):
    with pytest.raises(MultipleInvalid):
        REVOKE_API_KEY_SCHEMA(data)


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_sessions_schema(input_):
    assert VIEW_ALL_SESSIONS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_sessions_schema_failure(input_):
    with pytest.raises(MultipleInvalid):
        VIEW_ALL_SESSIONS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'data, expected', [
        ({'username': 'hi!', 'password': 'blah'},
         {'username': 'hi!', 'password': 'blah', 'persistent': False}),
        ({'username': 'lights', 'password': '12345', 'persistent': True},
         {'username': 'lights', 'password': '12345', 'persistent': True}),
    ])
def test_create_session_schema(data, expected):
    assert expected == CREATE_SESSION_SCHEMA(data)


@pytest.mark.parametrize(
    'username, password, persistence', [
        (b'{\xbe\xc9\xa9\x15s', b'U\xa5\x9e\xbd\x9b\xb0\xcfL', 'true'),
        (13313, False, True),
        ('lights', '12345', 'False'),
    ])
def test_create_session_schema_failure(username, password, persistence):
    with pytest.raises(MultipleInvalid):
        CREATE_SESSION_SCHEMA(dict(
            username=username,
            password=password,
            persistent=persistence,
            ))


@pytest.mark.parametrize(
    'data', [{'id': 'abcdefghij'}, {'id': '13082AFjaw'},
             {'id': '\x02\xb0\xc0AZ\xf2\x99\x22\x8b\xdc'}])
def test_expire_session_schema(data):
    assert data == EXPIRE_SESSION_SCHEMA(data)


@pytest.mark.parametrize(
    'data', [{'id': 1240312412}, {'id': None}])
def test_expire_session_schema_failure(data):
    with pytest.raises(MultipleInvalid):
        EXPIRE_SESSION_SCHEMA(data)
