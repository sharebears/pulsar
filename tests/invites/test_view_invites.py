import json

import pytest

from conftest import CODE_1, CODE_2, CODE_3, add_permissions, check_json_response
from pulsar import db
from pulsar.models import Invite, User


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
    """Viewing invites should return the invite."""
    add_permissions(app, 'view_invites')
    response = authed_client.get(f'/invites/{code}')
    check_json_response(response, expected)


def test_view_invites_multiple(app, authed_client):
    """Viewing the invite of a user should return a list of them."""
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
    """Including dead torrents in the list view should return dead invites."""
    add_permissions(app, 'view_invites')
    response = authed_client.get('/invites', query_string={'include_dead': True})
    assert len(response.get_json()['response']) == 3
    assert response.status_code == 200


def test_view_invites_used(app, authed_client):
    """Viewing only used invites should omit non-used invites."""
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
    """Viewing the invites of a nonexistent user should raise a 404."""
    add_permissions(app, 'view_invites', 'view_invites_others')
    response = authed_client.get('/invites/user/99')
    check_json_response(response, 'User 99 does not exist.')


def test_invite_user_with_code(app, authed_client):
    """
    Sending an invite when code is required should work, return an invite,
    and deduct an invite from the inviter.
    """
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
    """Sending an invite should clear the cache key for a user's list of invites."""
    app.config['REQUIRE_INVITE_CODE'] = True
    add_permissions(app, 'send_invites')
    Invite.from_inviter(1)  # Cache it

    authed_client.post('/invites', data=json.dumps({'email': 'bright@puls.ar'}))
    sent_invites = Invite.from_inviter(1, include_dead=True)
    assert len(sent_invites) == 4


def test_user_send_but_does_not_have_invite(app, authed_client):
    """Attempting to send an invite when the user has none should return an error."""
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
    """Sending an invite when open reg is on should error."""
    app.config['REQUIRE_INVITE_CODE'] = False
    add_permissions(app, 'send_invites')
    response = authed_client.post('/invites', data=json.dumps({'email': 'bright@puls.ar'}))
    check_json_response(response, 'An invite code is not required to register, '
                        'so invites have been disabled.')


@pytest.mark.parametrize(
    'code, expected, invites', [
        (CODE_1, {'expired': True}, 2),
        (CODE_2, f'Invite {CODE_2} does not exist.', 1),
        (CODE_3, f'Invite {CODE_3} does not exist.', 1),
        ('abc', f'Invite abc does not exist.', 1),
    ])
def test_revoke_invite(app, authed_client, code, expected, invites):
    """Revoking an invite should work only for active invites."""
    add_permissions(app, 'revoke_invites')
    response = authed_client.delete(f'/invites/{code}')
    user = User.from_id(1)
    check_json_response(response, expected)
    assert user.invites == invites
    if 'expired' in expected and expected['expired'] is True:
        invite = Invite.from_id(code, include_dead=True)
        assert invite.expired is True


def test_revoke_invite_others(app, authed_client):
    """
    Reovoking another's invite with the proper permissions should work and re-add
    the invite to the inviter's invite count.
    """
    add_permissions(app, 'revoke_invites', 'revoke_invites_others', 'view_invites_others')
    response = authed_client.delete(f'/invites/{CODE_3}')
    check_json_response(response, {'expired': True})
    user = User.from_id(2)
    assert user.invites == 1


def test_revoke_invite_others_failure(app, authed_client):
    """Revoking another's invite without permission should raise a 404."""
    add_permissions(app, 'revoke_invites')
    response = authed_client.delete(f'/invites/{CODE_3}')
    print(response.get_json())
    check_json_response(response, f'Invite {CODE_3} does not exist.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/invites', 'GET'),
        ('/invites/user/1', 'GET'),
        ('/invites', 'POST'),
        ('/invites/abc', 'DELETE'),
    ])
def test_route_permissions(authed_client, endpoint, method):
    """Make sure all routes are properly permissioned against the unpermissioned user."""
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
