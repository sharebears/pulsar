from pulsar import cache
from pulsar.models import ForumCategory


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
    assert ForumCategory.from_cache(category.cache_key).id == category.id == 5
