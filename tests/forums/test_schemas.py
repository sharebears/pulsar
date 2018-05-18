import pytest
from pulsar.forums.categories import ADD_FORUM_CATEGORY_SCHEMA, MODIFY_FORUM_CATEGORY_SCHEMA
from voluptuous import MultipleInvalid


@pytest.mark.parametrize(
    'data, response', [
        ({'name': 'NewForum', 'description': 'abba', 'position': 100},
         {'name': 'NewForum', 'description': 'abba', 'position': 100}),
        ({'name': 'asTr'}, {'name': 'asTr', 'description': None, 'position': 0}),
    ])
def test_schema_category_add(app, client, data, response):
    assert response == ADD_FORUM_CATEGORY_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({}, "required key not provided @ data['name']"),
        ({'name': 'NewForum', 'description': 123},
         "expected str for dictionary value @ data['description']"),
        ({'name': 'NewForum', 'position': b'balls'},
         "expected int for dictionary value @ data['position']"),
    ])
def test_schema_category_add_failure(app, client, data, error):
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
def test_schema_category_modify(app, client, data):
    assert data == MODIFY_FORUM_CATEGORY_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'name': 'NewForum', 'description': 123},
         "expected str for dictionary value @ data['description']"),
        ({'name': 'NewForum', 'position': b'balls'},
         "expected int for dictionary value @ data['position']"),
    ])
def test_schema_category_modify_failure(app, client, data, error):
    with pytest.raises(MultipleInvalid) as e:
        MODIFY_FORUM_CATEGORY_SCHEMA(data)
    assert str(e.value) == error
