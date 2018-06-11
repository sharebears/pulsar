
import pytest

from pulsar.mixins import SinglePKMixin
from pulsar.permissions.models import UserClass


def test_belongs_to_user_fails_authed(app, authed_client):
    """Base belongs_to_user fails when no User ID is set on the model."""
    mixin = SinglePKMixin()
    with app.test_request_context('/test'):
        assert not mixin.belongs_to_user()


def test_belongs_to_user_fails_unauthed(app, client):
    """Base belongs_to_user should always fail on unauthenticated users."""
    mixin = SinglePKMixin()
    setattr(mixin, 'user_id', 1)
    with app.test_request_context('/test'):
        assert not mixin.belongs_to_user()


def test_delet_unavailable_property_from_cache_doesnt_blow_up(app, authed_client):
    user = SinglePKMixin()
    user.del_property_cache('notakey')


@pytest.mark.parametrize(
    'data, result', [
        ('not-a-dict', False),
        ({'id': 1, 'name': 'User'}, False),
        ({'id': 1, 'name': 'User', 'permissions': ['a-perm'], 'forum_permissions': None}, True),
        ({'id': 1, 'name': 'User', 'permissions': ['a-perm'], 'has_users': False}, False),
     ])
def test_is_valid_data(app, client, data, result):
    """Make sure the post-cache fetch function for valid data works."""
    assert UserClass._valid_data(data) is result
