import pytest
from voluptuous import MultipleInvalid

from pulsar.forums.categories import (ADD_FORUM_CATEGORY_SCHEMA,
                                      MODIFY_FORUM_CATEGORY_SCHEMA)
from pulsar.forums.forums import (CREATE_FORUM_SCHEMA, MODIFY_FORUM_SCHEMA,
                                  VIEW_FORUM_SCHEMA)
from pulsar.forums.posts import CREATE_FORUM_POST_SCHEMA, MODIFY_FORUM_POST_SCHEMA
from pulsar.forums.threads import (CREATE_FORUM_THREAD_SCHEMA, MODIFY_FORUM_THREAD_SCHEMA,
                                   VIEW_FORUM_THREAD_SCHEMA)


@pytest.mark.parametrize(
    'data, response', [
        ({'name': 'NewForum', 'description': 'abba', 'position': 100},
         {'name': 'NewForum', 'description': 'abba', 'position': 100}),
        ({'name': 'asTr'}, {'name': 'asTr', 'description': None, 'position': 0}),
    ])
def test_schema_category_add(data, response):
    assert response == ADD_FORUM_CATEGORY_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({}, "required key not provided @ data['name']"),
        ({'name': 'NewForum', 'description': 123},
         "expected str for dictionary value @ data['description']"),
        ({'name': 'NewForum', 'position': b'balls'},
         "expected int for dictionary value @ data['position']"),
    ])
def test_schema_category_add_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        ADD_FORUM_CATEGORY_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'name': 'NewForum', 'description': 'abba', 'position': 0},
        {'name': 'asTr'},
        {'description': 'abc'},
        {},
    ])
def test_schema_category_modify(data):
    assert data == MODIFY_FORUM_CATEGORY_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'name': 'NewForum', 'description': 123},
         "expected str for dictionary value @ data['description']"),
        ({'name': 'NewForum', 'position': b'balls'},
         "expected int for dictionary value @ data['position']"),
    ])
def test_schema_category_modify_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        MODIFY_FORUM_CATEGORY_SCHEMA(data)
    assert str(e.value) == error


def test_view_forum_schema(data, error):
    pass
