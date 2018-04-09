import re
import pytest
from pulsar.utils import USERNAME_REGEX, PASSWORD_REGEX


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
