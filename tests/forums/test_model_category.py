from pulsar import cache, NewJSONEncoder
from pulsar.models import ForumCategory
from conftest import add_permissions, check_dictionary


def test_category_from_id(app, authed_client):
    category = ForumCategory.from_id(1)
    assert category.name == 'Site'
    assert category.description == 'General site discussion'


def test_category_cache(app, authed_client):
    category = ForumCategory.from_id(1)
    cache.cache_model(category, timeout=60)
    category = ForumCategory.from_id(1)
    assert category.name == 'Site'
    assert category.description == 'General site discussion'
    assert cache.ttl(category.cache_key) < 61


def test_category_get_all(app, authed_client):
    categories = ForumCategory.get_all()
    assert len(categories) == 3

    for category in categories:
        if category.name == 'Site' and category.id == 1:
            break
    else:
        raise AssertionError('A real forum not called')


def test_category_get_all_cached(app, authed_client):
    cache.set(ForumCategory.__cache_key_all__, ['1', '2', '3'], timeout=60)
    categories = ForumCategory.get_all()
    assert len(categories) == 2

    for category in categories:
        if category.name == 'Site' and category.id == 1:
            break
    else:
        raise AssertionError('A real forum not called')


def test_new_category(app, authed_client):
    category = ForumCategory.new(
        name='NewCategory',
        description=None,
        position=100)
    assert category.name == 'NewCategory'
    assert category.description is None
    assert category.position == 100
    assert ForumCategory.from_cache(category.cache_key).id == category.id == 6


def test_serialize_no_perms(app, client):
    category = ForumCategory.from_id(1)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 1,
        'name': 'Site',
        'description': 'General site discussion',
        'position': 1,
        })
    assert 'forums' in data and len(data['forums']) == 2
    assert len(data) == 5


def test_serialize_very_detailed(app, authed_client):
    add_permissions(app, 'modify_forums')
    category = ForumCategory.from_id(1)
    data = NewJSONEncoder()._to_dict(category)
    check_dictionary(data, {
        'id': 1,
        'name': 'Site',
        'description': 'General site discussion',
        'position': 1,
        'deleted': False,
        })
    assert 'forums' in data and len(data['forums']) == 2
    assert len(data) == 6


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'modify_forums')
    category = ForumCategory.from_id(1)
    data = NewJSONEncoder()._to_dict(category, nested=True)
    check_dictionary(data, {
        'id': 1,
        'name': 'Site',
        'description': 'General site discussion',
        'position': 1,
        'deleted': False,
        }, strict=True)
