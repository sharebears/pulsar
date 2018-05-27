from conftest import add_permissions
from pulsar import cache


def test_get_sections(app, authed_client):
    add_permissions(app, 'view_rules')
    response = authed_client.get('/rules').get_json()
    assert 'golden' in response['response']
    assert isinstance(response['response'], list)


def test_get_rules(app, authed_client):
    add_permissions(app, 'view_rules')
    response = authed_client.get('/rules/golden').get_json()
    assert isinstance(response['response'], dict)
    assert '1' in response['response']
    assert 'main' in response['response']['1']['1']


def test_get_rules_cache(app, authed_client, monkeypatch):
    add_permissions(app, 'view_rules')
    authed_client.get('/rules/golden')  # cache
    monkeypatch.setattr('pulsar.rules.os', None)
    response = authed_client.get('/rules/golden').get_json()
    assert isinstance(response['response'], dict)
    assert '1' in response['response']
    assert 'main' in response['response']['1']['1']
    assert cache.get('rules_golden')
    assert cache.ttl('rules_golden') is None
