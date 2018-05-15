import re
import pytest
from voluptuous import Invalid
from pulsar import USERNAME_REGEX, PASSWORD_REGEX
from pulsar.validators import bool_get


@pytest.mark.parametrize(
    'inputs, output', [
        ([True, '1', 'TruE', 'true'], True),
        ([False, '0', 'FaLsE', 'false'], False),
    ])
def test_bool_get(inputs, output):
    for input_ in inputs:
        assert output == bool_get(input_)


def test_bool_get_invalid():
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
    assert bool(re.match(USERNAME_REGEX, username)) == match


@pytest.mark.parametrize(
    'password, match', [
        ('abc45678#01', False),
        ('abcDEFgHI1342', False),
        ('183810*7aefj!', True),
        ('12348539#89131', False),
    ])
def test_password_regex(password, match):
    assert bool(re.match(PASSWORD_REGEX, password)) == match