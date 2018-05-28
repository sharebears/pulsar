import pytest

from conftest import CODE_1, CODE_2, CODE_3, add_permissions, check_dictionary
from pulsar import NewJSONEncoder, cache
from pulsar.auth.models import Session


def hex_generator(_):
    return next(HEXES)


def test_new_session(app):
    with app.app_context():
        session = Session.new(2, '127.0.0.2', 'ua-example')
        assert session.ip == '127.0.0.2'
        assert session.user_id == 2


def test_session_collision(app, monkeypatch):
    global HEXES
    HEXES = iter([CODE_2[:10], CODE_3[:10], CODE_3])
    monkeypatch.setattr('pulsar.auth.models.secrets.token_hex', hex_generator)
    with app.app_context():
        session = Session.new(2, '127.0.0.2', 'ua-example')
        assert session.hash != CODE_2[:10]
        assert session.csrf_token != CODE_2
        with pytest.raises(StopIteration):
            hex_generator(None)


def test_from_pk(app, client):
    session = Session.from_pk('abcdefghij')
    assert session.user_id == 1
    assert session.csrf_token == CODE_1


def test_from_pk_cached(app, client):
    session = Session.from_pk('abcdefghij')
    cache_key = cache.cache_model(session, timeout=60)
    session = Session.from_pk('abcdefghij')
    assert session.user_id == 1
    assert session.csrf_token == CODE_1
    assert cache.ttl(cache_key) < 61


def test_from_user(app, client):
    sessions = Session.from_user(1)
    assert len(sessions) == 2
    assert sessions[0].user_id == 1
    assert sessions[0].csrf_token == CODE_1


def test_from_user_cached(app, client):
    cache_key = Session.__cache_key_of_user__.format(user_id=1)
    sess = Session.from_pk('1234567890')  # noqa cache it
    cache.set(f'{cache_key}_incl_dead', ['1234567890'], timeout=60)
    sessions = Session.from_user(1, include_dead=True)
    assert len(sessions) == 1
    assert sessions[0].user_id == 2
    assert sessions[0].csrf_token == CODE_2


def test_from_pk_incl_dead(app, client):
    session = Session.from_pk('1234567890', include_dead=True)
    assert session.csrf_token == CODE_2


def test_get_nonexistent_session(app, client):
    session = Session.from_pk('1234567890')
    assert not session


def test_serialize_no_perms(app, client):
    session = Session.from_pk('abcdefghij')
    assert NewJSONEncoder()._to_dict(session) is None


def test_serialize_detailed(app, authed_client):
    add_permissions(app, 'view_sessions_others')
    session = Session.from_pk('1234567890', include_dead=True)
    data = NewJSONEncoder()._to_dict(session)
    check_dictionary(data, {
        'hash': '1234567890',
        'user_id': 2,
        'persistent': False,
        'ip': '0.0.0.0',
        'user_agent': None,
        'expired': True,
        })
    assert 'last_used' in data and isinstance(data['last_used'], int)
    assert len(data) == 7


def test_serialize_self(app, authed_client):
    session = Session.from_pk('abcdefghij')
    data = NewJSONEncoder()._to_dict(session)
    check_dictionary(data, {
        'hash': 'abcdefghij',
        'user_id': 1,
        'persistent': True,
        'ip': '0.0.0.0',
        'user_agent': None,
        'expired': False,
        })
    assert 'last_used' in data and isinstance(data['last_used'], int)
    assert len(data) == 7
