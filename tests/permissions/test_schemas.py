import pytest
from voluptuous import Invalid

from conftest import add_permissions
from pulsar.permissions.user_classes import (CREATE_USER_CLASS_SCHEMA,
                                             MODIFY_USER_CLASS_SCHEMA)


def test_create_user_class_schema(app, authed_client):
    data = {
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites'],
        }
    response_data = CREATE_USER_CLASS_SCHEMA(data)
    data['secondary'] = False
    assert response_data == data


@pytest.mark.parametrize(
    'data, error', [
        ({'name': 'user_v3', 'secondary': True, 'permissions': ['non_existent_permission']},
         "The following permissions are invalid: non_existent_permission, for dictionary "
         "value @ data['permissions']"),
    ])
def test_create_user_class_schema_failure(app, authed_client, data, error):
    with pytest.raises(Invalid) as e:
        CREATE_USER_CLASS_SCHEMA(data)
    assert str(e.value) == error


def test_modify_user_class_schema(app, authed_client):
    add_permissions(app, 'moderate_users_advanced')
    data = {
        'permissions': {
            'modify_permissions': False,
            'edit_settings': True
            },
        'secondary': True,
        }
    data == MODIFY_USER_CLASS_SCHEMA(data)
