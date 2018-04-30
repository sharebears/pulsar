from voluptuous import Invalid
from pulsar.utils import get_all_permissions


def permissions_dict(val):
    permissions = get_all_permissions()
    if isinstance(val, dict):
        for perm_name, action in val.items():
            if perm_name not in permissions:
                raise Invalid(f'{perm_name} is not a valid permission')
            elif not isinstance(action, bool):
                raise Invalid('permission actions must be booleans')
    else:
        raise Invalid('input value must be a dictionary')
    return val
