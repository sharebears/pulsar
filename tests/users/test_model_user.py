import mock
import pytest
from sqlalchemy.exc import IntegrityError

from conftest import add_permissions, check_dictionary, check_json_response
from pulsar import APIException, NewJSONEncoder, cache, db
from pulsar.users.models import User


def test_user_creation(app, client):
    """User creation should create a user object and populate default values."""
    user = User.new(
        username='bright',
        password='13579',
        email='bright@puls.ar')
    assert isinstance(user.id, int) and user.id > 1


def test_user_creation_dupe_username(app, client):
    """Creation of a user with dupe username should raise an APIException."""
    error_str = '<APIException (Code: 400) [Message: The username ligHts is already in use.]>'
    with pytest.raises(APIException) as e:
        User.new(
            username='ligHts',
            password='13579',
            email='bright@puls.ar')
    assert repr(e.value) == error_str


def test_user_creation_dupe_username_database(app, client):
    """
    Insertion of a user with duplicate username, regardless of case, should
    raise an IntegrityError.  """
    with pytest.raises(IntegrityError):
        db.session.execute(
            """INSERT INTO users (username, passhash, email) VALUES
            ('LiGhTs', '13579', 'bright@puls.ar')""")


def test_user_obj_from_id_and_username(app, client):
    """User objects should equal from both from_id and from_username."""
    user_id = User.from_id(1)
    user_name = User.from_username('lightS')
    assert repr(user_id) == f'<User 1>'
    assert user_id == user_name


def test_user_passwords(app, client):
    """Password setting and validation should work."""
    user = User.from_id(1)
    user.set_password('secure password')
    assert user.check_password('secure password')


def test_user_has_permission(app, client):
    """Test that user's has permission works."""
    add_permissions(app, 'sample_permission')
    user = User.from_id(1)
    assert user.has_permission('sample_permission')
    assert not user.has_permission('nonexistent_permission')


def test_user_permissions_property(app, client):
    """Permissions property should properly handle differences in userclasses and custom perms."""
    add_permissions(app, 'one', 'three', 'four')
    db.session.execute("""UPDATE user_classes SET permissions = '{"one", "five", "six", "four"}'""")
    db.session.execute("""UPDATE secondary_classes SET permissions = '{"five", "two", "one"}'""")
    db.session.execute("""INSERT INTO users_permissions VALUES (1, 'six', 'f')""")
    user = User.from_id(1)
    assert set(user.permissions) == {'four', 'one', 'two', 'five', 'three'}


def test_user_permissions_property_cached(app, client, monkeypatch):
    """Permissions property should properly handle differences in userclasses and custom perms."""
    add_permissions(app, 'one', 'three', 'four')
    user = User.from_id(1)
    assert set(user.permissions) == {'four', 'one', 'three'}
    assert cache.has(user.__cache_key_permissions__.format(id=user.id))
    del user
    with mock.patch('pulsar.users.models.User.user_class_model', None):
        user = User.from_id(1)
        assert set(user.permissions) == {'four', 'one', 'three'}


@pytest.mark.parametrize('uid, result', [(1, True), (2, False)])
def test_belongs_to_self(app, authed_client, uid, result):
    """Belong to self should return True if id == requester user id, else False."""
    user = User.from_id(uid)
    with app.test_request_context('/test'):
        assert user.belongs_to_user() is result


def test_locked_account_permissions(app, client):
    user = User.from_id(1)
    user.locked = True
    assert set(user.permissions) == {
        'view_staff_pm', 'send_staff_pm', 'resolve_staff_pm'}


def test_basic_permissions(app, client):
    add_permissions(app, 'create_forum_posts', 'list_user_classes')
    user = User.from_id(1)
    assert user.basic_permissions == ['create_forum_posts']


def test_locked_acc_perms_blocked(app, client):
    db.engine.execute("UPDATE users SET locked = 't' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_id'] = 'bcdefghijk'

    response = client.get('/users/1')
    check_json_response(response, 'Your account has been locked.')


def test_locked_acc_perms_can_access(app, client):
    db.engine.execute("UPDATE users SET locked = 't' where id = 2")
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['session_id'] = 'bcdefghijk'
    app.config['LOCKED_ACCOUNT_PERMISSIONS'] = 'view_users'

    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.get_json()['response']['id'] == 1


def test_serialize_no_perms(app, client):
    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user)
    check_dictionary(data, {
        'id': 1,
        'username': 'lights',
        'enabled': True,
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'uploaded': 5368709120,
        'downloaded': 0,
        }, strict=True)


def test_serialize_self(app, authed_client):
    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user)
    check_dictionary(data, {
        'id': 1,
        'username': 'lights',
        'email': 'lights@puls.ar',
        'enabled': True,
        'locked': False,
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'uploaded': 5368709120,
        'downloaded': 0,
        'invites': 1,
        'sessions': None,
        })
    assert ('api_keys' in data
            and len(data['api_keys']) == 1
            and data['api_keys'][0]['id'] == 'abcdefghij')
    assert len(data) == 12


def test_serialize_detailed(app, authed_client):
    add_permissions(app, 'moderate_users')
    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user)
    check_dictionary(data, {
        'id': 1,
        'username': 'lights',
        'email': 'lights@puls.ar',
        'enabled': True,
        'locked': False,
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'uploaded': 5368709120,
        'downloaded': 0,
        'invites': 1,
        'inviter': None,
        'sessions': None,
        'basic_permissions': None,
        })
    assert ('api_keys' in data
            and len(data['api_keys']) == 1
            and data['api_keys'][0]['id'] == 'abcdefghij')
    assert len(data) == 14


def test_serialize_very_detailed(app, authed_client):
    add_permissions(app, 'moderate_users', 'moderate_users_advanced')
    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user)
    check_dictionary(data, {
        'id': 1,
        'username': 'lights',
        'email': 'lights@puls.ar',
        'enabled': True,
        'locked': False,
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'uploaded': 5368709120,
        'downloaded': 0,
        'invites': 1,
        'inviter': None,
        'sessions': None,
        'basic_permissions': None,
        })
    assert ('api_keys' in data
            and len(data['api_keys']) == 1
            and data['api_keys'][0]['id'] == 'abcdefghij')
    assert 'permissions' in data and set(data['permissions']) == {
        'moderate_users', 'moderate_users_advanced'}
    assert len(data) == 15


def test_serialize_nested(app, authed_client):
    add_permissions(app, 'moderate_users')
    user = User.from_id(1)
    data = NewJSONEncoder()._to_dict(user, nested=True)
    check_dictionary(data, {
        'id': 1,
        'username': 'lights',
        'email': 'lights@puls.ar',
        'enabled': True,
        'locked': False,
        'user_class': 'User',
        'secondary_classes': ['FLS'],
        'uploaded': 5368709120,
        'downloaded': 0,
        'invites': 1,
        }, strict=True)
