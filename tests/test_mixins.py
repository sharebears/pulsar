import importlib

import pytest

from pulsar.mixins import SinglePKMixin
from pulsar.permissions.models import UserClass
from pulsar.utils.permissions import get_all_permissions


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


def test_all_models_permissions_are_valid():
    """Make sure that all model serialization permissions are valid permissions."""
    all_permissions = get_all_permissions()
    model_groups = [
        'auth',
        'forums',
        'invites',
        'permissions',
        'users'
        ]
    for mg in model_groups:
        models = importlib.import_module(f'pulsar.{mg}.models')
        classes = [cls for _, cls in models.__dict__.items() if
                   isinstance(cls, type) and issubclass(cls, SinglePKMixin)]
        for class_ in classes:
            permissions = (class_.__permission_detailed__, class_.__permission_very_detailed__, )
            for p in permissions:
                assert not p or p in all_permissions


def test_all_class_serialization_attributes_valid():
    """Make sure that all model serialization tuples are valid properties."""
    model_groups = [
        'auth',
        'forums',
        'invites',
        'permissions',
        'users'
        ]
    for mg in model_groups:
        models = importlib.import_module(f'pulsar.{mg}.models')
        classes = [cls for _, cls in models.__dict__.items() if
                   isinstance(cls, type) and issubclass(cls, SinglePKMixin)]
        for class_ in classes:
            attrs = class_.__dict__.keys()
            print(class_.__name__)
            serializes = (
                class_.__serialize__
                + class_.__serialize_self__
                + class_.__serialize_detailed__
                + class_.__serialize_very_detailed__)
            for s in serializes:
                assert s in attrs
