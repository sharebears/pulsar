import pytest
from voluptuous import Invalid

from pulsar import APIException
from pulsar.validators import val_invite_code, val_username


@pytest.mark.parametrize(
    'username', [
        123, '1234567890abcdefghijklmnoqrstuvwxyzabcdef', None
    ])
def test_username_validation_fail(app, client, username):
    with pytest.raises(Invalid) as e:
        val_username(username)
    assert str(e.value) == (
        'usernames must start with an alphanumeric character; can only contain '
        'alphanumeric characters, underscores, hyphens, and periods; and be '
        '32 characters or less')


def test_invite_code_validation_fail(app, client):
    app.config['REQUIRE_INVITE_CODE'] = True
    with pytest.raises(APIException) as e:
        val_invite_code(123)
    assert e.value.message == 'Invite code must be a 24 character string.'
