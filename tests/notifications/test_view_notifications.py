from conftest import add_permissions


def test_forum_subscriptions(app, authed_client):
    add_permissions(app, 'view_notifications', 'view_forums')
    subscripps = authed_client.get('/subscriptions').get_json()
    assert {3, 4} == set([t['id'] for t in subscripps['response']])


def test_forum_subscriptions_other(app, authed_client):
    add_permissions(app, 'view_notifications', 'view_notifications_others', 'view_forums')
    subscripps = authed_client.get('/subscriptions/user/2').get_json()
    assert [4] == [t['id'] for t in subscripps['response']]


def test_all_notifications(app, authed_client):
    add_permissions(app, 'view_notifications', 'view_forums')
    subscripps = authed_client.get('/notifications').get_json()
    assert {3, 4} == set([t['id'] for t in subscripps['response']['forum_subscriptions']])
