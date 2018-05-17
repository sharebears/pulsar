import pytest
from voluptuous import MultipleInvalid

from pulsar.users.moderate import moderate_user_schema


@pytest.mark.parametrize(
    'schema', [
        {'email': 'new@ema.il'},
        {'email': 'new@ema.il', 'password': 'abcdefGHIfJK12#'},
        {'downloaded': 123123123, 'invites': 104392},
    ])
def test_moderate_user_schema(schema):
    assert schema == moderate_user_schema(schema)


@pytest.mark.parametrize(
    'schema, error', [
        ({'email': 'new@ema.il', 'password': '1231233281FF'},
         "Password must be 12 or more characters and contain at least 1 letter, "
         "1 number, and 1 special character, for dictionary value @ data['password']"),
        ({'uploaded': 12313, 'extra': 0},
         "extra keys not allowed @ data['extra']"),
    ])
def test_moderate_user_schema_failure(schema, error):
    with pytest.raises(MultipleInvalid) as e:
        moderate_user_schema(schema)
    assert str(e.value) == error
