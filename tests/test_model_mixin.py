import pytest

import pulsar.models as models
from pulsar.mixins import ModelMixin
from pulsar.models import UserClass
from pulsar.utils.permissions import get_all_permissions


def test_default_cache_key_property(app, client, monkeypatch):
    """The cache key property should correctly format the key."""
    monkeypatch.setattr('pulsar.mixins.ModelMixin.__cache_key__', 'basemodel_{id}')
    mixin = ModelMixin()
    setattr(mixin, 'id', 2)
    assert 'basemodel_2' == mixin.cache_key


@pytest.mark.parametrize('patch', [True, False])
def test_default_cache_key_property_failure(app, client, monkeypatch, patch):
    """The cache key property should raise a NameError when cache key generation is invalid."""
    if patch:
        monkeypatch.setattr('pulsar.mixins.ModelMixin.__cache_key__', 'basemodel_{invalidkwarg}')
    mixin = ModelMixin()
    setattr(mixin, 'id', 2)
    with pytest.raises(NameError):
        assert 'basemodel_2' == mixin.cache_key


def test_belongs_to_user_works(app, authed_client):
    """Belongs to user works for User ID == flask.g.user.id!"""
    mixin = ModelMixin()
    setattr(mixin, 'user_id', 1)
    with app.test_request_context('/test'):
        assert mixin.belongs_to_user()


def test_belongs_to_user_fails_authed(app, authed_client):
    """Base belongs_to_user fails when no User ID is set on the model."""
    mixin = ModelMixin()
    with app.test_request_context('/test'):
        assert not mixin.belongs_to_user()


def test_belongs_to_user_fails_unauthed(app, client):
    """Base belongs_to_user should always fail on unauthenticated users."""
    mixin = ModelMixin()
    setattr(mixin, 'user_id', 1)
    with app.test_request_context('/test'):
        assert not mixin.belongs_to_user()


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
    classes = [cls for _, cls in models.__dict__.items() if
               isinstance(cls, type) and issubclass(cls, ModelMixin)]
    assert len(classes) > 10
    for class_ in classes:
        permissions = (class_.__permission_detailed__, class_.__permission_very_detailed__, )
        for p in permissions:
            assert not p or p in all_permissions


def test_all_class_serialization_attributes_valid():
    """Make sure that all model serialization tuples are valid properties."""
    classes = [cls for _, cls in models.__dict__.items() if
               isinstance(cls, type) and issubclass(cls, ModelMixin)]
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
