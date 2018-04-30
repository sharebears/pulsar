import pytest
from voluptuous import Invalid
from pulsar.users.validators import permissions_dict


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
