import secrets
from copy import copy
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import flask
from sqlalchemy import and_, func
from sqlalchemy.dialects.postgresql import ARRAY, INET
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.security import check_password_hash, generate_password_hash

from pulsar import APIException, cache, db
from pulsar.mixins import SinglePKMixin
from pulsar.permissions import BASIC_PERMISSIONS
from pulsar.users.serializers import APIKeySerializer, InviteSerializer, UserSerializer
from pulsar.utils import cached_property

if TYPE_CHECKING:
    from pulsar.permissions.models import UserClass as UserClass_  # noqa
    from pulsar.forums.models import Forum as Forum_, ForumThread as ForumThread_ # noqa


app = flask.current_app


class User(db.Model, SinglePKMixin):
    __tablename__ = 'users'
    __serializer__ = UserSerializer
    __cache_key__ = 'users_{id}'
    __cache_key_permissions__ = 'users_{id}_permissions'
    __cache_key_forum_permissions__ = 'users_{id}_forums_permissions'

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(32), unique=True, nullable=False)
    passhash: str = db.Column(db.String(128), nullable=False)
    email: str = db.Column(db.String(255), nullable=False)
    enabled: bool = db.Column(db.Boolean, nullable=False, server_default='t')
    locked: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    user_class_id: int = db.Column(
        db.Integer, db.ForeignKey('user_classes.id'), nullable=False, server_default='1')
    inviter_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    invites: int = db.Column(db.Integer, nullable=False, server_default='0')

    uploaded: int = db.Column(db.BigInteger, nullable=False, server_default='5368709120')  # 5 GB
    downloaded: int = db.Column(db.BigInteger, nullable=False, server_default='0')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_users_username', func.lower(cls.username), unique=True),
                db.Index('ix_users_email', func.lower(cls.email)))

    @classmethod
    def from_username(cls, username: str) -> 'User':
        username = username.lower()
        user = cls.query.filter(func.lower(cls.username) == username).scalar()
        cache.cache_model(user)
        return user

    @classmethod
    def new(cls,
            username: str,
            password: str,
            email: str) -> 'User':
        """
        Alternative constructor which generates a password hash and
        lowercases and strips leading and trailing spaces from the email.
        """
        if cls.from_username(username) is not None:
            raise APIException(f'The username {username} is already in use.')
        return super()._new(
            username=username,
            passhash=generate_password_hash(password),
            email=email.lower().strip())

    @cached_property
    def user_class(self):
        return self.user_class_model.name

    @cached_property
    def secondary_classes(self) -> List[str]:
        from pulsar.permissions.models import SecondaryClass
        secondary_classes = SecondaryClass.from_user(self.id)
        return [sc.name for sc in secondary_classes]

    @cached_property
    def inviter(self) -> Optional['User']:
        return User.from_pk(self.inviter_id) if self.inviter_id else None

    @cached_property
    def api_keys(self) -> List['APIKey']:
        return APIKey.from_user(self.id)

    @cached_property
    def permissions(self) -> List[str]:
        if self.locked:  # Locked accounts have restricted permissions.
            return app.config['LOCKED_ACCOUNT_PERMISSIONS']
        from pulsar.permissions.models import UserPermission
        return self._get_permissions(
            key=self.__cache_key_permissions__.format(id=self.id),
            model=UserPermission,
            attr='permissions')

    @cached_property
    def forum_permissions(self) -> List[str]:
        from pulsar.permissions.models import ForumPermission
        return self._get_permissions(
            key=self.__cache_key_forum_permissions__.format(id=self.id),
            model=ForumPermission,
            attr='forum_permissions')

    def _get_permissions(self,
                         key: str,
                         model: db.Model,
                         attr: str) -> List[str]:
        """
        A general function to get the permissions of a user from a permission
        model and attributes of their user classes.

        :param key:   The cache key to cache the permissions under
        :param model: The model to query custom permissions from
        :param attr:  The attribute of the userclasses that should be queried
        """
        from pulsar.permissions.models import SecondaryClass
        permissions = cache.get(key)
        if not permissions:
            permissions = copy(getattr(self.user_class_model, attr))
            for class_ in SecondaryClass.from_user(self.id):
                permissions += getattr(class_, attr)
            permissions = set(permissions)  # De-dupe

            for perm, granted in model.from_user(self.id).items():
                if not granted and perm in permissions:
                    permissions.remove(perm)
                if granted and perm not in permissions:
                    permissions.add(perm)

            cache.set(key, permissions)
        return permissions

    @cached_property
    def basic_permissions(self) -> List[str]:
        return [p for p in self.permissions if p in BASIC_PERMISSIONS]

    @cached_property
    def user_class_model(self) -> 'UserClass_':
        from pulsar.permissions.models import UserClass
        return UserClass.from_pk(self.user_class_id)

    def belongs_to_user(self) -> bool:
        """Check whether or not the requesting user matches this user."""
        return flask.g.user == self

    def set_password(self, password: str) -> None:
        self.passhash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.passhash, password)

    def has_permission(self, permission: Optional[str]) -> bool:
        """Check whether a user has a permission. Includes regular and forum permissions."""
        return (permission is not None
                and permission in self.permissions.union(self.forum_permissions))


class Invite(db.Model, SinglePKMixin):
    __tablename__: str = 'invites'
    __serializer__ = InviteSerializer
    __cache_key__: str = 'invites_{code}'
    __cache_key_of_user__: str = 'invites_user_{user_id}'
    __deletion_attr__ = 'expired'

    code: str = db.Column(db.String(24), primary_key=True)
    inviter_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invitee_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    email: str = db.Column(db.String(255), nullable=False)
    time_sent: datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    from_ip: str = db.Column(INET, nullable=False, server_default='0.0.0.0')
    expired: bool = db.Column(db.Boolean, nullable=False, index=True, server_default='f')

    @classmethod
    def new(cls,
            inviter_id: int,
            email: str,
            ip: int) -> 'Invite':
        """
        Generate a random invite code.

        :param inviter_id: User ID of the inviter
        :param email:      E-mail to send the invite to
        :param ip:         IP address the invite was sent from
        """
        while True:
            code = secrets.token_hex(12)
            if not cls.from_pk(code, include_dead=True):
                break
        cache.delete(cls.__cache_key_of_user__.format(user_id=inviter_id))
        return super()._new(
            inviter_id=inviter_id,
            code=code,
            email=email.lower().strip(),
            from_ip=ip)

    @classmethod
    def from_inviter(cls,
                     inviter_id: int,
                     include_dead: bool = False,
                     used: bool = False) -> List['Invite']:
        """
        Get all invites sent by a user.

        :param inviter_id:   The User ID of the inviter.
        :param include_dead: Whether or not to include dead invites in the list
        :param used:         Whether or not to include used invites in the list

        :return:             A list of invites sent by the inviter
        """
        filter = cls.inviter_id == inviter_id
        if used:
            filter = and_(filter, cls.invitee_id.isnot(None))  # type: ignore
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=inviter_id),
            filter=filter,
            order=cls.time_sent.desc(),  # type: ignore
            include_dead=include_dead or used)

    @cached_property
    def invitee(self) -> User:
        return User.from_pk(self.invitee_id)

    @cached_property
    def inviter(self) -> User:
        return User.from_pk(self.inviter_id)

    def belongs_to_user(self) -> bool:
        """Returns whether or not the requesting user matches the inviter."""
        return flask.g.user is not None and self.inviter_id == flask.g.user.id


class APIKey(db.Model, SinglePKMixin):
    __tablename__: str = 'api_keys'
    __serializer__ = APIKeySerializer
    __cache_key__: str = 'api_keys_{hash}'
    __cache_key_of_user__: str = 'api_keys_user_{user_id}'
    __deletion_attr__ = 'revoked'

    hash: str = db.Column(db.String(10), primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    keyhashsalt: str = db.Column(db.String(128))
    last_used: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip: str = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent: str = db.Column(db.Text)
    revoked: bool = db.Column(db.Boolean, nullable=False, index=True, server_default='f')
    permissions: str = db.Column(ARRAY(db.String(36)))

    @classmethod
    def new(cls,
            user_id: int,
            ip: str,
            user_agent: str,
            permissions: List[str] = None) -> Tuple[str, 'APIKey']:
        """
        Create a new API Key with randomly generated secret keys and the
        user details passed in as params. Generated keys are hashed and
        salted for storage in the database.

        :param user_id:    API Key will belong to this user
        :param ip:         The IP that this session was created with
        :param user_agent: User Agent the session was created with

        :return:           A tuple containing the identifier and the new API Key
        """
        while True:
            hash = secrets.token_hex(5)
            if not cls.from_pk(hash, include_dead=True):
                break
        key = secrets.token_hex(8)
        cache.delete(cls.__cache_key_of_user__.format(user_id=user_id))
        api_key = super()._new(
            user_id=user_id,
            hash=hash,
            keyhashsalt=generate_password_hash(key),
            ip=ip,
            user_agent=user_agent,
            permissions=permissions or [])
        return (hash + key, api_key)

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

    @classmethod
    def hashes_from_user(cls, user_id: int) -> List[Union[int, str]]:
        return cls.get_pks_of_many(
            key=cls.__cache_key_of_user__.format(user_id=user_id),
            filter=cls.user_id == user_id)

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

        user = User.from_pk(self.user_id)
        return user.has_permission(permission)
