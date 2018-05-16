import secrets
from datetime import datetime
from typing import List, Optional, Tuple

import pytz
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY, INET
from werkzeug.security import check_password_hash, generate_password_hash

from pulsar import cache, db
from pulsar.users.models import User


class Session(db.Model):
    __tablename__ = 'sessions'
    __cache_key__ = 'sessions_{id}'
    __cache_key_of_user__ = 'sessions_user_{user_id}'

    __serialize_self__ = __serialize_detailed__ = (
        'id',
        'user_id',
        'persistent',
        'last_used',
        'ip',
        'user_agent',
        'expired')

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
    def new(cls,
            user_id: int,
            ip: str,
            user_agent: str,
            persistent: bool = False) -> 'Session':
        """
        Create a new session with randomly generated secret keys and the
        user details passed in as params.

        :param user_id:    Session will belong to this user
        :param ip:         IP the session was created with
        :param user_agent: User Agent the session was created with
        :param persistent: Whether or not to persist the session

        :return:           The new Session
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
    def from_user(cls,
                  user_id: int,
                  include_dead: bool = False) -> List['Session']:
        """
        Get all sessions owned by a user.

        :param user_id:      The User ID of the owner
        :param include_dead: Whether or not to include dead API keys in the search

        :return:             A list of APIKey objects owned by the user
        """
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=user_id),
            filter=cls.user_id == user_id,
            include_dead=include_dead)

    def is_expired(self) -> bool:
        """Checks whether or not the session is expired."""
        if self.expired:
            return True
        elif not self.persistent:
            delta = datetime.utcnow().replace(tzinfo=pytz.utc) - self.last_used
            if delta.total_seconds() > 60 * 30:  # 30 minutes
                self.expired = True
                db.session.commit()
                return True
        return False

    @staticmethod
    def expire_all_of_user(user_id) -> None:
        """
        Expire all active sessions that belong to a user.

        :param user_id: The User ID of the user whose sessions will be expired
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
        'id',
        'user_id',
        'last_used',
        'ip',
        'user_agent',
        'revoked',
        'permissions')

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
    def new(cls,
            user_id: int,
            ip: str,
            user_agent: str,
            permissions: Optional[List[str]] = None) -> Tuple[str, 'APIKey']:
        """
        Create a new API Key with randomly generated secret keys and the
        user details passed in as params. Generated keys are hashed and
        salted for storage in the database.

        :param user_id:    Session will belong to this user
        :param ip: IP      The IP that this session was created with
        :param user_agent: User Agent the session was created with

        :return:           A tuple containing the identifier and the new API Key
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
            permissions=permissions or [])
        return (id + key, api_key)

    @classmethod
    def from_user(cls,
                  user_id: int,
                  include_dead: bool = False) -> List['APIKey']:
        """
        Get all API keys owned by a user.

        :param user_id:      The User ID of the owner
        :param include_dead: Whether or not to include dead API keys in the search

        :return:             A list of API keys owned by the user
        """
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=user_id),
            filter=cls.user_id == user_id,
            include_dead=include_dead)

    def check_key(self, key: str) -> bool:
        """
        Validates the authenticity of an API key against its stored id.

        :param key: The key to check against the keyhashsalt
        :return:    Whether or not the key matches the keyhashsalt
        """
        return check_password_hash(self.keyhashsalt, key)

    def has_permission(self, permission: str) -> bool:
        """
        Checks if the API key is assigned a permission. If the API key
        is not assigned any permissions, it checks against the user's
        permissions instead.

        :param permission: Permission to search for
        :return:           Whether or not the API Key has the permission
        """
        if self.permissions:
            return permission in self.permissions

        user = User.from_id(self.user_id)
        return permission in user.permissions

    @staticmethod
    def revoke_all_of_user(user_id: int) -> None:
        """
        Revokes all active API keys of a user.

        :param user_id: The User ID of the user whose API keys will be revoked
        """
        ids = db.session.query(APIKey.id).filter(APIKey.revoked == 'f').all()
        for id in ids:
            cache.delete(APIKey.__cache_key__.format(id=id[0]))

        db.session.query(APIKey).filter(
            APIKey.user_id == user_id
            ).update({'revoked': True})
