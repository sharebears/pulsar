import pytest
from sqlalchemy.exc import IntegrityError

from conftest import check_dictionary
from pulsar import APIException, NewJSONEncoder, cache, db
from pulsar.permissions.models import SecondaryClass, UserClass


@pytest.mark.parametrize(
    'class_, name', [
        (UserClass, 'UsEr'), (SecondaryClass, 'Fls')
    ])
def test_create_dupe_user_classes(app, client, class_, name):
    with pytest.raises(APIException):
        class_.new(
            name=name,
            permissions=None)


@pytest.mark.parametrize(
    'class_, name', [
        ('user_classes', 'USeR'), ('secondary_classes', 'fLS')
    ])
def test_create_dupe_user_classes_database(app, client, class_, name):
    with pytest.raises(IntegrityError):
        db.session.execute(f"INSERT INTO {class_} (name) VALUES ('{name}')")


@pytest.mark.parametrize(
    'class_, class_id, permission', [
        (UserClass, 1, 'edit_settings'),
        (SecondaryClass, 1, 'send_invites'),
    ])
def test_user_class_cache(app, client, class_, class_id, permission):
    user_class = class_.from_pk(class_id)
    cache_key = cache.cache_model(user_class, timeout=60)
    user_class = class_.from_pk(class_id)
    assert user_class.id == class_id
    assert permission in user_class.permissions
    assert cache.ttl(cache_key) < 61


@pytest.mark.parametrize(
    'class_', [UserClass, SecondaryClass])
def test_user_class_cache_get_all(app, client, class_):
    cache.set(class_.__cache_key_all__, [2], timeout=60)
    all_user_classes = class_.get_all()
    assert len(all_user_classes) == 1
    assert 'edit_settings' in all_user_classes[0].permissions


def test_user_secondary_classes_models(app, client):
    cache.set(SecondaryClass.__cache_key_of_user__.format(id=1), [2], timeout=60)
    secondary_classes = SecondaryClass.from_user(1)
    assert len(secondary_classes) == 1
    assert secondary_classes[0].name == 'user_v2'


def test_serialize_user_class_permless(app, client):
    user_class = UserClass.from_pk(1)
    data = NewJSONEncoder().default(user_class)
    check_dictionary(data, {
        'id': 1,
        'name': 'User',
        })


def test_serialize_user_class_detailed(app, authed_client):
    user_class = UserClass.from_pk(1)
    data = NewJSONEncoder().default(user_class)
    check_dictionary(data, {
        'id': 1,
        'name': 'User',
        'permissions': ['modify_permissions', 'edit_settings'],
        'forum_permissions': [],
        }, strict=True)
