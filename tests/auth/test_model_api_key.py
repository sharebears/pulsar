import pytest

from conftest import CODE_1, CODE_2, CODE_3
from pulsar import cache, db
from pulsar.auth.models import APIKey


def hex_generator(_):
    return next(HEXES)


def test_new_key(app, client):
    raw_key, api_key = APIKey.new(2, '127.0.0.2', 'UA')
    assert len(raw_key) == 26
    assert api_key.ip == '127.0.0.2'
    assert api_key.user_id == 2


def test_api_key_collision(app, client, monkeypatch):
    # First four are the the id and csrf_token, last one is the 16char key.
    global HEXES
    HEXES = iter([CODE_2[:10], CODE_3[:10], CODE_1[:16]])
    monkeypatch.setattr('pulsar.models.secrets.token_hex', hex_generator)

    raw_key, api_key = APIKey.new(2, '127.0.0.2', 'UA')
    assert len(raw_key) == 26
    assert api_key.id != CODE_2[:10]
    with pytest.raises(StopIteration):
        hex_generator(None)


def test_from_id_and_check(app, client):
    api_key = APIKey.from_id('abcdefghij')
    assert api_key.user_id == 1
    assert api_key.check_key(CODE_1)
    assert not api_key.check_key(CODE_2)


def test_from_id_when_dead(app, client):
    api_key = APIKey.from_id('1234567890', include_dead=True)
    assert api_key.user_id == 2
    assert api_key.check_key(CODE_2)


def test_api_key_revoke_all(app, client):
    APIKey.revoke_all_of_user(1)
    db.session.commit()
    api_key = APIKey.from_id('abcdefghij', include_dead=True)
    assert api_key.revoked


def test_api_key_revoke_all_cache(client):
    api_key = APIKey.from_id('abcdefghij')
    cache_key = cache.cache_model(api_key, timeout=60)
    assert cache.ttl(cache_key) < 61
    APIKey.revoke_all_of_user(1)
    db.session.commit()
    api_key = APIKey.from_id('abcdefghij', include_dead=True)
    assert api_key.revoked is True
    assert cache.ttl(cache_key) > 61


def test_api_key_permission(app, client):
    api_key = APIKey.from_id('abcdefghij', include_dead=True)
    assert api_key.has_permission('sample_permission')
    assert not api_key.has_permission('not_a_permission')
