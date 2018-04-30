import pytest
from voluptuous import Invalid
from conftest import add_permissions
from pulsar.auth.validators import permissions_list


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
