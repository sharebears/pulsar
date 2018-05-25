from pulsar.users.models import User


def test_cached_property(app, client, monkeypatch):
    """Test that cached property doesn't re-access the function."""
    user = User.from_pk(1)
    assert user.user_class == 'User'
    monkeypatch.setattr('pulsar.users.models.User.user_class_model', None)
    assert user.user_class == 'User'
