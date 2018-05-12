from .permissions import *  # noqa
from .validation import *  # noqa

USERNAME_REGEX = r'^[A-Za-z0-9][A-Za-z0-9_\-\.]*$'
PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[$@$!%*#?&]).{12,}$'


def many_to_dict(li_):
    return [l.to_dict() for l in li_]
