import pytest
from pulsar import BaseModel
from pulsar.models import User
from pulsar.utils.permissions import get_all_permissions


@pytest.mark.parametrize(
    'data, result', [
        ('not-a-dict', False),
        ({'id': 1, 'username': 'lights'}, False),
     ])
def test_is_valid_data(app, client, data, result):
    assert User._valid_data(data) is result


def test_all_models_permissions_are_valid():
    import pulsar.models as models
    all_permissions = get_all_permissions()
    classes = [cls for _, cls in models.__dict__.items() if
               isinstance(cls, type) and issubclass(cls, BaseModel)]
    assert len(classes) > 10
    for class_ in classes:
        permissions = (class_.__permission_detailed__, class_.__permission_very_detailed__, )
        for p in permissions:
            assert not p or p in all_permissions


def test_all_class_serialization_attributes_valid():
    import pulsar.models as models
    classes = [cls for _, cls in models.__dict__.items() if
               isinstance(cls, type) and issubclass(cls, BaseModel)]
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
