import secrets
import pulsar.users.models  # noqa
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET, ARRAY
from werkzeug.security import generate_password_hash, check_password_hash
from pulsar import db


class Session(db.Model):
    __tablename__ = 'sessions'

    hash = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    persistent = db.Column(db.Boolean, nullable=False, server_default='f')
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    csrf_token = db.Column(db.String(24), nullable=False)
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')

    user = relationship('User', back_populates='sessions', uselist=False, lazy=False)

    @classmethod
    def generate_session(cls, user_id, ip, user_agent, persistent=False):
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
            hash = secrets.token_hex(5)
            if not cls.from_hash(hash, include_dead=True):
                break
        csrf_token = secrets.token_hex(12)
        return cls(
            user_id=user_id,
            hash=hash,
            csrf_token=csrf_token,
            ip=ip,
            user_agent=user_agent,
            persistent=persistent,
            )

    @classmethod
    def from_hash(cls, hash, include_dead=False):
        """
        Get a session from it's hash.

        :param str hash: The hash of the session
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            sessions in the search

        :return: A ``Session`` object or ``None``
        """
        query = cls.query.filter(cls.hash == hash)
        if not include_dead:
            query = query.filter(cls.active == 't')
        return query.one_or_none()

    @staticmethod
    def expire_all_of_user(user_id):
        db.session.query(Session).filter(
            Session.user_id == user_id
            ).update({'active': False})


class APIKey(db.Model):
    __tablename__ = 'api_keys'

    hash = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    keyhashsalt = db.Column(db.String(128))
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')
    permissions = db.Column(ARRAY(db.String(32)))

    user = relationship('User', back_populates='api_keys', uselist=False, lazy=False)

    @classmethod
    def generate_key(cls, user_id, ip, user_agent, permissions=[]):
        """
        Create a new API Key with randomly generated secret keys and the
        user details passed in as params.

        :param int user_id: Session will belong to this user
        :param str ip: IP the session was created with
        :param str user_agent: User Agent the session was created with

        :return: An ``APIKey`` object
        """
        while True:
            hash = secrets.token_hex(5)
            if not cls.from_hash(hash, include_dead=True):
                break
        key = secrets.token_hex(8)
        return (hash + key, cls(
            user_id=user_id,
            hash=hash,
            keyhashsalt=generate_password_hash(key),
            ip=ip,
            user_agent=user_agent,
            permissions=permissions,
            ))

    @classmethod
    def from_hash(cls, hash, include_dead=False):
        """
        Get an API key from it's hash.

        :param str hash: The hash of the API key
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            API keys in the search

        :return: An ``APIKey`` object or ``None``
        """
        query = cls.query.filter(cls.hash == hash)
        if not include_dead:
            query = query.filter(cls.active == 't')
        return query.one_or_none()

    def check_key(self, key):
        """
        Validates the authenticity of an API key against its stored hash.

        :param str key: The key to check against the hash
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
        return permission in self.user.permissions

    @staticmethod
    def revoke_all_of_user(user_id):
        """
        Revokes all active API keys of a user.

        :param int user_id: API keys of this user will be revoked
        """
        db.session.query(APIKey).filter(
            APIKey.user_id == user_id
            ).update({'active': False})
