import json
import pytest
from conftest import check_json_response, add_permissions, CODE_1, CODE_2, CODE_3
from pulsar import db
from pulsar.users.models import User
from pulsar.invites.models import Invite


def hex_generator(_):
    return next(HEXES)


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO invites (inviter_id, email, code, active) VALUES
        (1, 'bright@puls.ar', '{CODE_1}', 't'),
        (1, 'bright@quas.ar', '{CODE_2}', 'f'),
        (2, 'bright@puls.ar', '{CODE_3}', 't')
         """)
    yield
    db.engine.execute("DELETE FROM invites")


def test_invite_collision(app, monkeypatch):
    global HEXES
    HEXES = iter([CODE_1, '098765432109876543211234'])
    monkeypatch.setattr('pulsar.invites.models.secrets.token_hex', hex_generator)
    with app.app_context():
        invite = Invite.generate_invite(2, 'bitsu@puls.ar', '127.0.0.2')
        assert invite.code != CODE_1
        with pytest.raises(StopIteration):
            hex_generator(None)


@pytest.mark.parametrize(
    'code, expected', [
        (CODE_1, {
            'active': True,
            'code': CODE_1,
            'email': 'bright@puls.ar',
            'invitee': None,
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
        'active': True,
        'code': CODE_1,
        'email': 'bright@puls.ar',
        'invitee': None,
        }, list_=True)
    assert response.status_code == 200


def test_nonexistent_user(app, authed_client):
    add_permissions(app, 'view_invites', 'view_invites_others')
    response = authed_client.get('/invites/user/99')
    check_json_response(response, 'User 99 does not exist.')


def test_invite_user_with_code(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = True
    add_permissions(app, 'send_invites')
    response = authed_client.post('/invites', data=json.dumps({
        'email': 'bright@puls.ar'}))
    user = User.from_id(1)
    check_json_response(response, {
        'active': True,
        'email': 'bright@puls.ar',
        'invitee': None,
        })
    assert response.status_code == 200
    assert user.invites == 0


def test_does_not_have_invite(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = True
    add_permissions(app, 'send_invites')
    db.engine.execute('UPDATE users SET invites = 0')
    db.session.commit()
    response = authed_client.post('/invites', data=json.dumps({
        'email': 'bright@puls.ar'}))
    check_json_response(response, 'You do not have an invite to send.')
    assert response.status_code == 400


def test_invite_without_code(app, authed_client):
    app.config['REQUIRE_INVITE_CODE'] = False
    add_permissions(app, 'send_invites')
    response = authed_client.post('/invites', data=json.dumps(
        dict(email='bright@puls.ar')))
    check_json_response(response, 'An invite code is not required to register, '
                        'so invites have been disabled.')


@pytest.mark.parametrize(
    'code, expected, invites', [
        (CODE_1, {'active': False}, 2),
        (CODE_2, f'Invite {CODE_2} does not exist.', 1),
        ('abc', f'Invite abc does not exist.', 1),
    ])
def test_revoke_invite(app, authed_client, code, expected, invites):
    add_permissions(app, 'revoke_invites')
    response = authed_client.delete(f'/invites/{code}')
    user = User.from_id(1)
    check_json_response(response, expected)
    assert user.invites == invites


def test_view_invitees(app, authed_client):
    add_permissions(app, 'view_invites')
    response = authed_client.get('/invitees')
    check_json_response(response, {
        'id': 2, 'username': 'paffu'
        }, list_=True)
    assert response.status_code == 200


def test_view_invitees_blank(app, authed_client):
    add_permissions(app, 'view_invites', 'view_invites_others')
    response = authed_client.get('/invitees/user/2')
    check_json_response(response, [], list_=True, strict=True)
    assert response.status_code == 200


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/invites', 'GET'),
        ('/invites', 'POST'),
        ('/invites/abc', 'DELETE'),
        ('/invitees', 'GET'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'Resource does not exist.')
    assert response.status_code == 404
