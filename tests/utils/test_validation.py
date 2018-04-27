import pytest
from voluptuous import Schema, Invalid
from conftest import check_json_response, add_permissions
from pulsar.utils import bool_get, validate_data, permissions_list, permissions_dict


def test_invalid_schema(app, authed_client):
    @app.route('/test_schema', methods=['POST'])
    @validate_data(Schema({
        'required_arg': int}))
    def test_schema(required_arg):
        return 'never hit this'

    response = authed_client.post('/test_schema', json={'required_arg': 'not-an-int'})
    check_json_response(response, 'Invalid data: expected int (key "required_arg")')


@pytest.mark.parametrize(
    'inputs, output', [
        ([True, '1', 'TruE', 'true'], True),
        ([False, '0', 'FaLsE', 'false'], False),
    ])
def test_bool_get(inputs, output):
    for input_ in inputs:
        assert output == bool_get(input_)


def test_bool_get_invalid():
    for input_ in [1, 0, 'Yes', 'No', '11']:
        with pytest.raises(Invalid):
            bool_get(input_)


def test_permissions_list(app, authed_client):
    permissions = ['sample_one', 'sample_two']
    add_permissions(app, *permissions)
    assert permissions == permissions_list(permissions)


def test_permissions_list_failure(app, authed_client):
    permissions = ['sample_one', 'sample_two']
    add_permissions(app, 'sample_one', 'sample_three')
    with pytest.raises(Invalid) as e:
        permissions_list(permissions)
    assert str(e.value) == 'permissions must be in the user\'s permissions list'


def test_permissions_dict():
    permissions = {
        'manipulate_permissions': True,
        'view_invites': True,
    }
    assert permissions == permissions_dict(permissions)


@pytest.mark.parametrize(
    'permissions, expected', [
        ({'change_password': 'false', 'view_invites': True},
         'permission actions must be booleans'),
        ({'change_wasspord': True, 'view_invites': False},
         'change_wasspord is not a valid permission'),
        ('not-a-dict', 'input value must be a dictionary'),
    ])
def test_permissions_dict_failure(permissions, expected):
    with pytest.raises(Invalid) as e:
        permissions_dict(permissions)
    assert str(e.value) == expected
