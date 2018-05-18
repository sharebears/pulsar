import pytest

from conftest import CODE_1, CODE_2, CODE_3, CODE_4, add_permissions, check_dictionary
from pulsar import NewJSONEncoder, cache
from pulsar.invites.models import Invite


def hex_generator(_):
    return next(HEXES)


def test_get_invite(app, client):
    """Basic invite getting."""
    invite = Invite.from_id(CODE_1)
    assert invite.inviter_id == 1
    assert invite.email == 'bright@puls.ar'


@pytest.mark.parametrize(
    'inviter_id, include_dead, used, invites', [
        (1, False, False, {CODE_1}),
        (1, True, False, {CODE_1, CODE_2, CODE_4}),
        (1, False, True, {CODE_2}),
        (1, True, True, {CODE_2}),
    ])
def test_invites_from_inviter(app, client, inviter_id, include_dead, used, invites):
    """Invites by the inviter and the available parameters."""
    assert invites == set(i.id for i in Invite.from_inviter(
        inviter_id=inviter_id,
        include_dead=include_dead,
        used=used))


def test_invites_from_inviter_cached(app, client):
    """Test the usage of the inviter cache key."""
    cache_key = Invite.__cache_key_of_user__.format(user_id=1)
    cache.set(cache_key, [CODE_3], timeout=60)
    invites = Invite.from_inviter(1)
    assert len(invites) == 1
    assert invites[0].id == CODE_3
    assert cache.ttl(cache_key) < 61


def test_invite_creation_collision(app, monkeypatch):
    """
    Make sure that unique codes are generated and that collisions are
    properly handled.
    """
    global HEXES
    HEXES = iter([CODE_1, '098765432109876543211234'])
    monkeypatch.setattr('pulsar.models.secrets.token_hex', hex_generator)
    with app.app_context():
        invite = Invite.new(2, 'bitsu@puls.ar', '127.0.0.2')
        assert invite.id != CODE_1
        with pytest.raises(StopIteration):
            hex_generator(None)


@pytest.mark.parametrize('inv_id, result', [(CODE_1, True), (CODE_3, False)])
def test_belongs_to_user(app, authed_client, inv_id, result):
    """Test that the belongs_to_user function works."""
    invite = Invite.from_id(inv_id)
    with app.test_request_context('/test'):
        assert invite.belongs_to_user() is result


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
