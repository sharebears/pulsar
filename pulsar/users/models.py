from copy import copy
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import secrets

import flask
from sqlalchemy import func, and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import INET
from werkzeug.security import check_password_hash, generate_password_hash

from pulsar import APIException, cache, db
from pulsar.mixins import SinglePKMixin
from pulsar.permissions import BASIC_PERMISSIONS
from pulsar.utils import cached_property
from pulsar.users.serializers import UserSerializer, InviteSerializer

if TYPE_CHECKING:
    from pulsar.auth.models import APIKey as APIKey_  # noqa
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
    def api_keys(self) -> List['APIKey_']:
        from pulsar.auth.models import APIKey
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
