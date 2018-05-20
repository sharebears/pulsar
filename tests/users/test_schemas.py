import re

import pytest
from voluptuous import MultipleInvalid

from pulsar.users.users import CREATE_USER_SCHEMA
from pulsar.users.moderate import MODERATE_USER_SCHEMA
from pulsar.users.settings import SETTINGS_SCHEMA
from pulsar.users.validators import USERNAME_REGEX, PASSWORD_REGEX


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


@pytest.mark.parametrize(
    'data, result', [
        ({'username': 'plights',
          'password': '13abcdefGHIjK!#@!)',
          'email': 'hi@puls.ar'},
         {'username': 'plights',
          'password': '13abcdefGHIjK!#@!)',
          'email': 'hi@puls.ar',
          'code': None}),
        ({'username': 'heLLLO',
          'password': 'heLLLomyPass0or^d',
          'email': 'hello@quas.ar',
          'code': 'astr'},
         {'username': 'heLLLO',
          'password': 'heLLLomyPass0or^d',
          'email': 'hello@quas.ar',
          'code': 'astr'})
    ])
def test_create_user_schema(data, result):
    assert result == CREATE_USER_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'username': 'plights', 'password': None, 'email': 'hi@puls.ar'},
         "expected string or buffer for dictionary value @ data['password']"),
        ({'username': 'plights', 'password': 'abc', 'email': 'hi@puls.ar'},
         "Password must be between 12 and 512 characters and contain at least 1 letter, "
         "1 number, and 1 special character for dictionary value @ data['password']"),
        ({'username': 'plights', 'email': 'hi@puls.ar'},
         "required key not provided @ data['password']"),
        ({'username': 'liGhts', 'password': 'heLLLomyPass0or^d', 'email': 'hello@quas.ar'},
         "another user already has the username liGhts for dictionary value @ data['username']")
    ])
def test_create_user_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        CREATE_USER_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'schema', [
        {'email': 'new@ema.il'},
        {'email': 'new@ema.il', 'password': 'abcdefGHIfJK12#'},
        {'downloaded': 123123123, 'invites': 104392},
    ])
def test_moderate_user_schema(schema):
    assert schema == MODERATE_USER_SCHEMA(schema)


@pytest.mark.parametrize(
    'schema, error', [
        ({'email': 'new@ema.il', 'password': '1231233281FF'},
         "Password must be between 12 and 512 characters and contain at least 1 letter, "
         "1 number, and 1 special character for dictionary value @ data['password']"),
        ({'uploaded': 12313, 'extra': 0},
         "extra keys not allowed @ data['extra']"),
    ])
def test_moderate_user_schema_failure(schema, error):
    with pytest.raises(MultipleInvalid) as e:
        MODERATE_USER_SCHEMA(schema)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'existing_password': 'apassword', 'new_password': 'eafoij!3ir31A'},
    ])
def test_settings_schema(data):
    assert data == SETTINGS_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'existing_password': 'apassword', 'new_password': 'eafoiA'},
         "Password must be between 12 and 512 characters and contain at least 1 letter, "
         "1 number, and 1 special character for dictionary value @ data['new_password']"),
        ({'existing_password': 'word', 'new_password': 'eafoiA'},
         "length of value must be at least 5 for dictionary value @ data['existing_password']"),
    ])
def test_settings_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        SETTINGS_SCHEMA(data)
    assert str(e.value) == error
