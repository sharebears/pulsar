from typing import TYPE_CHECKING, List, Optional

import flask
from sqlalchemy import func
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.security import check_password_hash, generate_password_hash

from pulsar import APIException, cache, db

if TYPE_CHECKING:
    from pulsar.auth.models import APIKey as APIKey_, Session as Session_  # noqa
    from pulsar.permissions.models import UserClass as UserClass_  # noqa

app = flask.current_app


class User(db.Model):
    __tablename__ = 'users'
    __cache_key__ = 'users_{id}'
    __cache_key_permissions__ = 'users_{id}_permissions'

    __serialize__ = (
        'id',
        'username',
        'enabled',
        'user_class',
        'secondary_classes',
        'uploaded',
        'downloaded')
    __serialize_self__ = (
        'email',
        'locked',
        'invites',
        'sessions',
        'api_keys')
    __serialize_detailed__ = (
        'email',
        'locked',
        'invites',
        'inviter',
        'sessions',
        'api_keys')
    __serialize_nested_exclude__ = (
        'inviter',
        'sessions',
        'api_keys')

    __permission_detailed__ = 'moderate_users'
    __permission_very_detailed__ = 'moderate_users_advanced'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, server_default='t')
    locked = db.Column(db.Boolean, nullable=False, server_default='f')
    user_class_id = db.Column(
        db.Integer, db.ForeignKey('user_classes.id'), nullable=False, server_default='1')
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    invites = db.Column(db.Integer, nullable=False, server_default='0')

    uploaded = db.Column(db.BigInteger, nullable=False, server_default='5368709120')  # 5 GB
    downloaded = db.Column(db.BigInteger, nullable=False, server_default='0')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_users_username', func.lower(cls.username), unique=True),
                db.Index('ix_users_email', func.lower(cls.email)))

    @classmethod
    def from_username(cls, username: str) -> 'User':
        username = username.lower()
        user = cls.query.filter(func.lower(cls.username) == username).first()
        cache.cache_model(user)
        return user

    @classmethod
    def new(cls, username: str, password: str, email: str) -> 'User':
        """
        Alternative constructor which generates a password hash and
        lowercases and strips leading and trailing spaces from the email.
        """
        if cls.from_username(username) is not None:
            raise APIException(f'The username {username} is already in use.')
        return super().new(
            username=username,
            passhash=generate_password_hash(password),
            email=email.lower().strip())

    @property
    def user_class(self) -> 'UserClass_':
        from pulsar.permissions.models import UserClass
        return UserClass.from_id(self.user_class_id)

    @property
    def secondary_classes(self) -> List[str]:
        from pulsar.permissions.models import SecondaryClass
        secondary_classes = SecondaryClass.from_user(self.id)
        return [sc.name for sc in secondary_classes]

    @property
    def inviter(self) -> Optional['User']:
        return User.from_id(self.inviter_id) if self.inviter_id else None

    @property
    def api_keys(self) -> List['APIKey_']:
        from pulsar.auth.models import APIKey
        return APIKey.from_user(self.id)

    @property
    def sessions(self) -> List['Session_']:
        from pulsar.auth.models import Session
        return Session.from_user(self.id)

    @property
    def permissions(self) -> List[str]:
        if self.locked:  # Locked accounts have restricted permissions.
            return app.config['LOCKED_ACCOUNT_PERMISSIONS']

        from pulsar.permissions.models import SecondaryClass, UserPermission
        cache_key = self.__cache_key_permissions__.format(id=self.id)
        permissions = cache.get(cache_key)
        if not permissions:
            permissions = self.user_class.permissions or []
            for class_ in SecondaryClass.from_user(self.id):
                permissions += class_.permissions or []
            permissions = list(set(permissions))  # De-dupe

            for perm, granted in UserPermission.from_user(self.id).items():
                if not granted and perm in permissions:
                    permissions.remove(perm)
                if granted and perm not in permissions:
                    permissions.append(perm)

            cache.set(cache_key, permissions)
        return permissions

    def belongs_to_user(self):
        """Check whether or not the requesting user matches this user."""
        return flask.g.user == self

    def set_password(self, password: str) -> None:
        self.passhash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.passhash, password)

    def has_permission(self, permission: Optional[str]) -> bool:
        return permission is not None and permission in self.permissions
