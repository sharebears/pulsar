from conftest import add_permissions


def test_forum_subscriptions(app, authed_client):
    add_permissions(app, 'view_notifications', 'view_forums')
    subscripps = authed_client.get('/subscriptions').get_json()
    assert len(subscripps['response']) == 2
    assert {3, 4} == set([t['id'] for t in subscripps['response']])
