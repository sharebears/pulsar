import json

import pytest

from conftest import (CODE_1, CODE_2, CODE_3, add_permissions,
                      check_json_response)
from pulsar import cache, db
from pulsar.models import Invite, User


def hex_generator(_):
    return next(HEXES)


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO invites (inviter_id, invitee_id, email, id, expired) VALUES
        (1, NULL, 'bright@puls.ar', '{CODE_1}', 'f'),
        (1, 2, 'bright@quas.ar', '{CODE_2}', 't'),
        (2, NULL, 'bright@puls.ar', '{CODE_3}', 'f')
         """)
    yield
    db.engine.execute("DELETE FROM invites")


def test_get_invite(app, client):
    invite = Invite.from_id(CODE_1)
    cache.cache_model(invite, timeout=60)
    invite = invite.from_id(CODE_1)
    assert invite.inviter_id == 1
    assert invite.email == 'bright@puls.ar'


def test_get_invite_from_inviter(app, client):
    cache_key = Invite.__cache_key_of_user__.format(user_id=1)
    cache.set(cache_key, [CODE_3], timeout=60)
    invites = Invite.from_inviter(1)
    assert len(invites) == 1
    assert invites[0].id == CODE_3
    assert cache.ttl(cache_key) < 61


def test_invite_creation_collision(app, monkeypatch):
    global HEXES
    HEXES = iter([CODE_1, '098765432109876543211234'])
    monkeypatch.setattr('pulsar.models.secrets.token_hex', hex_generator)
    with app.app_context():
        invite = Invite.new(2, 'bitsu@puls.ar', '127.0.0.2')
        assert invite.id != CODE_1
        with pytest.raises(StopIteration):
            hex_generator(None)


@pytest.mark.parametrize(
    'code, expected', [
        (CODE_1, {
            'expired': False,
            'id': CODE_1,
            'email': 'bright@puls.ar',
            'invitee': None,
            }),
        (CODE_2, {
            'expired': True,
            'id': CODE_2,
            'email': 'bright@quas.ar',
            }),
        ('abcdef', 'Invite abcdef does not exist.')
    ])
def test_view_invite(app, authed_client, code, expected):
    add_permissions(app, 'view_invites')
    response = authed_client.get(f'/invites/{code}')
    check_json_response(response, expected)


def test_view_invites(app, authed_client):
    add_permissions(app, 'view_invites')
    response = authed_client.get('/invites')
    check_json_response(response, {
        'expired': False,
        'id': CODE_1,
        'email': 'bright@puls.ar',
        'invitee': None,
        }, list_=True)
    assert len(response.get_json()['response']) == 1
    assert response.status_code == 200


def test_view_invites_include_dead(app, authed_client):
    add_permissions(app, 'view_invites')
    response = authed_client.get('/invites', query_string={'include_dead': True})
    assert len(response.get_json()['response']) == 2
    assert response.status_code == 200


def test_view_invites_used(app, authed_client):
    add_permissions(app, 'view_invites')
    response = authed_client.get('/invites', query_string={'used': True})
    check_json_response(response, {
        'expired': True,
        'id': CODE_2,
        'email': 'bright@quas.ar',
        }, list_=True)
    assert len(response.get_json()['response']) == 1
    assert response.status_code == 200


def test_view_invites_of_nonexistent_user(app, authed_client):
    add_permissions(app, 'view_invites', 'view_invites_others')
    response = authed_client.get('/invites/user/99')
    check_json_response(response, 'User 99 does not exist.')


def test_invite_user_with_code(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = True
    add_permissions(app, 'send_invites')
    response = authed_client.post(
        '/invites', data=json.dumps({'email': 'bright@puls.ar'}),
        content_type='application/json')
    check_json_response(response, {
        'expired': False,
        'email': 'bright@puls.ar',
        'invitee': None,
        })
    assert response.status_code == 200

    user = User.from_id(1)
    assert user.invites == 0


def test_invites_list_cache_clear(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = True
    add_permissions(app, 'send_invites')
    Invite.from_inviter(1)  # Cache it

    authed_client.post('/invites', data=json.dumps({'email': 'bright@puls.ar'}))
    sent_invites = Invite.from_inviter(1, include_dead=True)
    assert len(sent_invites) == 3


def test_user_send_but_does_not_have_invite(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = True
    add_permissions(app, 'send_invites')
    db.engine.execute('UPDATE users SET invites = 0')
    db.session.commit()
    response = authed_client.post(
        '/invites', data=json.dumps({'email': 'bright@puls.ar'}),
        content_type='application/json')
    check_json_response(response, 'You do not have an invite to send.')
    assert response.status_code == 400


def test_invite_without_code(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = False
    add_permissions(app, 'send_invites')
    response = authed_client.post('/invites', data=json.dumps({'email': 'bright@puls.ar'}))
    check_json_response(response, 'An invite code is not required to register, '
                        'so invites have been disabled.')


@pytest.mark.parametrize(
    'code, expected, invites', [
        (CODE_1, {'expired': True}, 2),
        (CODE_2, f'Invite {CODE_2} does not exist.', 1),
        ('abc', f'Invite abc does not exist.', 1),
    ])
def test_revoke_invite(app, authed_client, code, expected, invites):
    add_permissions(app, 'revoke_invites')
    response = authed_client.delete(f'/invites/{code}')
    user = User.from_id(1)
    check_json_response(response, expected)
    assert user.invites == invites
    if 'expired' in expected and expected['expired'] is True:
        invite = Invite.from_id(code, include_dead=True)
        assert invite.expired is True


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/invites', 'GET'),
        ('/invites/user/1', 'GET'),
        ('/invites', 'POST'),
        ('/invites/abc', 'DELETE'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
