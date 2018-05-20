import pytest
from voluptuous import MultipleInvalid

from pulsar.invites.invites import USER_INVITE_SCHEMA, VIEW_INVITES_SCHEMA


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
    with pytest.raises(MultipleInvalid):
        VIEW_INVITES_SCHEMA(data)


def test_user_invite_schema():
    assert {'email': 'aemail@puls.ar'} == USER_INVITE_SCHEMA({
        'email': 'aemail@puls.ar'})


def test_user_invite_schema_failure():
    with pytest.raises(MultipleInvalid) as e:
        USER_INVITE_SCHEMA({'email': 'aemail@pulsar'})
    assert str(e.value) == "expected an Email for dictionary value @ data['email']"
