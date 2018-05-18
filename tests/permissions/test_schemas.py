import pytest
from voluptuous import Invalid


def test_create_user_class_schema(app, authed_client):
    from pulsar.permissions.user_classes import create_user_class_schema
    data = {
        'name': 'user_v3',
        'permissions': ['edit_settings', 'send_invites'],
        }
    response_data = create_user_class_schema(data)
    data['secondary'] = False
    assert response_data == data


@pytest.mark.parametrize(
    'data, error', [
        ({'name': 'user_v3', 'secondary': True, 'permissions': ['non_existent_permission']},
         "The following permissions are invalid: non_existent_permission, for dictionary "
         "value @ data['permissions']"),
    ])
def test_create_user_class_schema_failure(app, authed_client, data, error):
    from pulsar.permissions.user_classes import create_user_class_schema
    with pytest.raises(Invalid) as e:
        create_user_class_schema(data)
    assert str(e.value) == error


def test_modify_user_class_schema(app, authed_client):
    from pulsar.permissions.user_classes import modify_user_class_schema
    data = {
        'permissions': {
            'modify_permissions': False,
            'edit_settings': True
            },
        'secondary': True,
        }
    data == modify_user_class_schema(data)
