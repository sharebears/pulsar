import pytest
from voluptuous import Invalid

from pulsar.invites.invites import VIEW_INVITES_SCHEMA


@pytest.mark.parametrize(
    'data', [
        {'used': '1'},
        {'include_dead': True},
        {'used': False, 'include_dead': 'false'},
    ])
def test_invite_schema_pass(data):
    VIEW_INVITES_SCHEMA(data)


@pytest.mark.parametrize(
    'data', [
        {'used': '2', 'include_dead': 2},
        {'used': True, 'include_dead': True, 'third': False},
    ])
def test_invite_schema_fail(data):
    with pytest.raises(Invalid):
        VIEW_INVITES_SCHEMA(data)
