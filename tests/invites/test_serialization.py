from conftest import CODE_1, CODE_3, add_permissions, check_dictionary
from pulsar.invites.models import Invite
from pulsar.serializer import NewJSONEncoder


def test_serialize_no_perms(app, authed_client):
    invite = Invite.from_id(CODE_3)
    assert NewJSONEncoder()._to_dict(invite) is None


def test_serialize_self(app, authed_client):
    invite = Invite.from_id(CODE_1)
    data = NewJSONEncoder()._to_dict(invite)
    check_dictionary(data, {
        'id': CODE_1,
        'email': 'bright@puls.ar',
        'expired': False,
        'invitee': None})
    assert isinstance(data['time_sent'], int)
    assert len(data) == 5


def test_serialize_detailed(app, authed_client):
    add_permissions(app, 'view_invites_others')
    invite = Invite.from_id(CODE_1)
    data = NewJSONEncoder()._to_dict(invite)
    check_dictionary(data, {
        'id': CODE_1,
        'email': 'bright@puls.ar',
        'expired': False,
        'invitee': None,
        'from_ip': '0.0.0.0'})
    assert isinstance(data['time_sent'], int)
    assert isinstance(data['inviter'], dict)
    assert len(data) == 7


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'view_invites_others')
    invite = Invite.from_id(CODE_1)
    data = NewJSONEncoder()._to_dict(invite, nested=True)
    check_dictionary(data, {
        'id': CODE_1,
        'email': 'bright@puls.ar',
        'expired': False,
        'invitee': None,
        'from_ip': '0.0.0.0'})
    assert isinstance(data['time_sent'], int)
    assert len(data) == 6
