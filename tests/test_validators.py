import re

import pytest
from voluptuous import Invalid

from pulsar import PASSWORD_REGEX, USERNAME_REGEX
from pulsar.validators import bool_get


@pytest.mark.parametrize(
    'inputs, output', [
        ([True, '1', 'TruE', 'true'], True),
        ([False, '0', 'FaLsE', 'false'], False),
    ])
def test_bool_get(inputs, output):
    """Bool get accepts all provided values."""
    for input_ in inputs:
        assert output == bool_get(input_)


def test_bool_get_invalid():
    """bool_get only accepts 1/0 true/false string/booleans."""
    for input_ in [1, 0, 'Yes', 'No', '11']:
        with pytest.raises(Invalid):
            bool_get(input_)


@pytest.mark.parametrize(
    'username, match', [
        ('abc', True),
        ('1', True),
        ('-hello', False),
        ('hel-lo', True),
    ])
def test_username_regex(username, match):
    """Username regex should not accept invalid values."""
    assert bool(re.match(USERNAME_REGEX, username)) == match


@pytest.mark.parametrize(
    'password, match', [
        ('abc45678#01', False),
        ('abcDEFgHI1342', False),
        ('183810*7aefj!', True),
        ('12348539#89131', False),
    ])
def test_password_regex(password, match):
    """Password regex should not accept crap strings."""
    assert bool(re.match(PASSWORD_REGEX, password)) == match
