import pytest
from voluptuous import LengthInvalid

from conftest import add_permissions
from pulsar.validators import PostLength


def test_post_length_override(app, authed_client):
    add_permissions(app, 'no_post_length_limit')
    assert 'hello' == PostLength(max=3)('hello')


def test_post_length_fail(app, authed_client):
    with pytest.raises(LengthInvalid):
        PostLength(max=3)('hello')
