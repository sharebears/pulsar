import pytest
from voluptuous import Invalid, MultipleInvalid

from pulsar.auth.api_keys import VIEW_ALL_API_KEYS_SCHEMA
from pulsar.auth.sessions import CREATE_SESSION_SCHEMA, VIEW_ALL_SESSIONS_SCHEMA


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_api_keys_schema(input_):
    assert VIEW_ALL_API_KEYS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_api_keys_schema_failure(input_):
    with pytest.raises(MultipleInvalid):
        assert not VIEW_ALL_API_KEYS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', ['1', 'true', False])
def test_view_all_sessions_schema(input_):
    assert VIEW_ALL_SESSIONS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'input_', [0, '2', '\x01'])
def test_view_all_sessions_schema_failure(input_):
    with pytest.raises(MultipleInvalid):
        assert not VIEW_ALL_SESSIONS_SCHEMA({'include_dead': input_})


@pytest.mark.parametrize(
    'username, password, persistence', [
        (b'{\xbe\xc9\xa9\x15s', b'U\xa5\x9e\xbd\x9b\xb0\xcfL', 'true'),
        (13313, False, True),
        ('lights', '12345', 'False'),
    ])
def test_schema_failure(username, password, persistence):
    with pytest.raises(Invalid):
        CREATE_SESSION_SCHEMA(dict(
            username=username,
            password=password,
            persistent=persistence,
            ))


# TODO: Login Schema pass
