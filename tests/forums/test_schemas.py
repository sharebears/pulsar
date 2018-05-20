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


@pytest.mark.parametrize(
    'data', [
        {'page': 2, 'include_dead': False},
        {'limit': 100},
    ])
def test_view_forum_and_thread_schema(data):
    for schema in [VIEW_FORUM_SCHEMA, VIEW_FORUM_THREAD_SCHEMA]:
        assert data == schema(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'page': '2'}, "expected int for dictionary value @ data['page']"),
        ({'limit': 99}, "value is not allowed for dictionary value @ data['limit']"),
    ])
def test_view_forum_schema_failure(data, error):
    for schema in [VIEW_FORUM_SCHEMA, VIEW_FORUM_THREAD_SCHEMA]:
        with pytest.raises(MultipleInvalid) as e:
            VIEW_FORUM_SCHEMA(data)
        assert str(e.value) == error


@pytest.mark.parametrize(
    'data, result', [
        ({'name': 'testname', 'category_id': 3},
         {'name': 'testname', 'category_id': 3, 'description': None, 'position': 0}),
        ({'name': 'testname', 'category_id': 3, 'description': 'longtext', 'position': 4},
         {'name': 'testname', 'category_id': 3, 'description': 'longtext', 'position': 4}),
    ])
def test_create_forum_schema(data, result):
    assert result == CREATE_FORUM_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'name': 'testname', 'category_id': '3'},
         "expected int for dictionary value @ data['category_id']"),
        ({'category_id': 6}, "required key not provided @ data['name']"),
        ({'name': 'foirjfopiqewjfpoaifeoiaofewifjaof', 'category_id': 5},
         "length of value must be at most 32 for dictionary value @ data['name']"),
    ])
def test_create_forum_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        CREATE_FORUM_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'name': 'newname', 'description': None},
        {'position': 10000, 'category_id': 100},
    ])
def test_modify_forum_schema(data):
    assert data == MODIFY_FORUM_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'name': None, 'category_id': 2}, "expected str for dictionary value @ data['name']"),
        ({'description': False}, "expected str for dictionary value @ data['description']"),
    ])
def test_modify_forum_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        MODIFY_FORUM_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'topic': 'testtopic', 'forum_id': 3},
    ])
def test_create_thread_schema(data):
    assert data == CREATE_FORUM_THREAD_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'topic': 'testname', 'forum_id': '3'},
         "expected int for dictionary value @ data['forum_id']"),
        ({'forum_id': 6}, "required key not provided @ data['topic']"),
    ])
def test_create_thread_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        CREATE_FORUM_THREAD_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'topic': 'testname', 'forum_id': 160},
        {'locked': True, 'sticky': False},
    ])
def test_modify_forum_thread_schema(data):
    assert data == MODIFY_FORUM_THREAD_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'topic': None, 'forum_id': 160},
         "expected str for dictionary value @ data['topic']"),
        ({'forum_id': None},
         "expected int for dictionary value @ data['forum_id']"),
        ({'locked': '2', 'sticky': False},
         """boolean must be "1", "true", "0", or "false" (case insensitive) for """
         """dictionary value @ data['locked']"""),
    ])
def test_modify_forum_thread_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        MODIFY_FORUM_THREAD_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'contents': 'hello', 'thread_id': 100},
    ])
def test_create_post_schema(data):
    assert data == CREATE_FORUM_POST_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'contents': None}, "expected str for dictionary value @ data['contents']"),
        ({'thread_id': 99}, "required key not provided @ data['contents']"),
        ({'contents': '99', 'thread_id': None},
         "expected int for dictionary value @ data['thread_id']"),
    ])
def test_create_post_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        CREATE_FORUM_POST_SCHEMA(data)
    assert str(e.value) == error


@pytest.mark.parametrize(
    'data', [
        {'contents': 'hello', 'sticky': False},
        {'sticky': False},
    ])
def test_modify_post_schema(data):
    assert data == MODIFY_FORUM_POST_SCHEMA(data)


@pytest.mark.parametrize(
    'data, error', [
        ({'contents': None, 'sticky': True},
         "expected str for dictionary value @ data['contents']"),
        ({'sticky': 99}, "expected bool for dictionary value @ data['sticky']"),
        ({'contents': '99', 'sticky': None},
         "expected bool for dictionary value @ data['sticky']"),
    ])
def test_modify_post_schema_failure(data, error):
    with pytest.raises(MultipleInvalid) as e:
        MODIFY_FORUM_POST_SCHEMA(data)
    assert str(e.value) == error
