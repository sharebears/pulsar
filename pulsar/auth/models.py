import pytz
import flask
import secrets
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import INET, ARRAY
from werkzeug.security import generate_password_hash, check_password_hash
from pulsar import db, cache


class Session(db.Model):
    __tablename__ = 'sessions'
    __cache_key__ = 'sessions_{id}'
    __cache_key_of_user__ = 'sessions_user_{user_id}'

    __serialize_self__ = __serialize_detailed__ = (
        'id', 'user_id', 'persistent', 'last_used', 'ip', 'user_agent', 'expired')

    __permission_detailed__ = 'view_sessions_others'

    id = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    persistent = db.Column(db.Boolean, nullable=False, server_default='f')
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    csrf_token = db.Column(db.String(24), nullable=False)
    expired = db.Column(db.Boolean, nullable=False, index=True, server_default='f')

    @classmethod
    def new(cls, user_id, ip, user_agent, persistent=False):
        """
        Create a new session with randomly generated secret keys and the
        user details passed in as params.

        :param int user_id: Session will belong to this user
        :param str ip: IP the session was created with
        :param str user_agent: User Agent the session was created with
        :param bool persistent: Whether or not to persist the session

        :return: A ``Session`` object
        """
        while True:
            id = secrets.token_hex(5)
            if not cls.from_id(id):
                break
        csrf_token = secrets.token_hex(12)
        cache.delete(cls.__cache_key_of_user__.format(user_id=user_id))
        return super().new(
            user_id=user_id,
            id=id,
            csrf_token=csrf_token,
            ip=ip,
            user_agent=user_agent,
            persistent=persistent)

    @classmethod
    def from_user(cls, user_id, include_dead=False):
        """
        Get all sessions owned by a user.

        :param int user_id: The User ID of the owner.
        :param bool include_dead: (Default ``False``) Whether or not to
            include dead API keys in the search

        :return: A ``list`` of ``APIKey`` objects
        """
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=user_id),
            filter=cls.user_id == user_id,
            include_dead=include_dead)

    def belongs_to_user(self):
        return flask.g.user and self.user_id == flask.g.user.id

    def is_expired(self):
        if self.expired:
            return True
        elif not self.persistent:
            delta = datetime.utcnow().replace(tzinfo=pytz.utc) - self.last_used
            if delta.total_seconds() > 60 * 30:  # 30 minutes
                self.expired = True
                db.session.commit()
                self.clear_cache()
                return True
        return False

    @staticmethod
    def expire_all_of_user(user_id):
        """
        Expire all active sessions that belong to a user.

        :param int user_id: The expired sessions belong to this user
        """
        ids = db.session.query(Session.id).filter(Session.expired == 'f').all()
        for id in ids:
            cache.delete(Session.__cache_key__.format(id=id[0]))

        db.session.query(Session).filter(
            Session.user_id == user_id
            ).update({'expired': True})


class APIKey(db.Model):
    __tablename__ = 'api_keys'
    __cache_key__ = 'api_keys_{id}'
    __cache_key_of_user__ = 'api_keys_user_{user_id}'

    __serialize_self__ = __serialize_detailed__ = (
        'id', 'user_id', 'last_used', 'ip', 'user_agent', 'revoked', 'permissions')

    __permission_detailed__ = 'view_api_keys_others'

    id = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    keyhashsalt = db.Column(db.String(128))
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    revoked = db.Column(db.Boolean, nullable=False, index=True, server_default='f')
    permissions = db.Column(ARRAY(db.String(32)))

    @classmethod
    def new(cls, user_id, ip, user_agent, permissions=[]):
        """
        Create a new API Key with randomly generated secret keys and the
        user details passed in as params.

        :param int user_id: Session will belong to this user
        :param str ip: IP the session was created with
        :param str user_agent: User Agent the session was created with

        :return: An ``APIKey`` object
        """
        while True:
            id = secrets.token_hex(5)
            if not cls.from_id(id, include_dead=True):
                break
        key = secrets.token_hex(8)
        cache.delete(cls.__cache_key_of_user__.format(user_id=user_id))
        api_key = super().new(
            user_id=user_id,
            id=id,
            keyhashsalt=generate_password_hash(key),
            ip=ip,
            user_agent=user_agent,
            permissions=permissions)
        return (id + key, api_key)

    @classmethod
    def from_user(cls, user_id, include_dead=False):
        """
        Get all API keys owned by a user.

        :param int user_id: The User ID of the owner.
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            API keys in the search

        :return: A ``list`` of ``APIKey`` objects
        """
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=user_id),
            filter=cls.user_id == user_id,
            include_dead=include_dead)

    def belongs_to_user(self):
        return flask.g.user and self.user_id == flask.g.user.id

    def check_key(self, key):
        """
        Validates the authenticity of an API key against its stored id.

        :param str key: The key to check against the id
        :return: ``True`` if it matches, ``False`` if it doesn't
        """
        return check_password_hash(self.keyhashsalt, key)

    def has_permission(self, permission):
        """
        Checks if the API key is assigned a permission. If the API key
        is not assigned any permissions, it checks against the user's
        permissions instead.

        :param str permission: Permission to search for
        :return: ``True`` if permission is present, ``False`` if not
        """
        if self.permissions:
            return permission in self.permissions

        from pulsar.models import User
        user = User.from_id(self.user_id)
        return permission in user.permissions

    @staticmethod
    def revoke_all_of_user(user_id):
        """
        Revokes all active API keys of a user.

        :param int user_id: API keys of this user will be revoked
        """
        ids = db.session.query(APIKey.id).filter(APIKey.revoked == 'f').all()
        for id in ids:
            cache.delete(APIKey.__cache_key__.format(id=id[0]))

        db.session.query(APIKey).filter(
            APIKey.user_id == user_id
            ).update({'revoked': True})
