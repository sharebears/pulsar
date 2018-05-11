import flask
import pulsar.invites.models  # noqa
import pulsar.permissions.models  # noqa
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.sql import select
from sqlalchemy.ext.declarative import declared_attr
from pulsar import db, cache

app = flask.current_app


class User(db.Model):
    __tablename__ = 'users'
    __cache_key__ = 'users_{id}'
    __cache_key_permissions__ = 'users_permissions_{id}'
    __cache_key_secondary_classes__ = 'users_secondary_classes_{id}'
    __serializable_attrs__ = ('id', 'username', 'enabled', 'locked', 'user_class',
                              'secondary_classes', 'uploaded', 'downloaded')
    __serializable_attrs_detailed__ = ('email', 'invites', 'sessions', 'api_keys')
    __serializable_attrs_very_detailed__ = ('inviter', )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, server_default='t')
    locked = db.Column(db.Boolean, nullable=False, server_default='f')
    user_class = db.Column(
        db.String, db.ForeignKey('user_classes.name'), nullable=False, server_default='User')
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    invites = db.Column(db.Integer, nullable=False, server_default='0')

    uploaded = db.Column(db.BigInteger, nullable=False, server_default='5368709120')  # 5 GB
    downloaded = db.Column(db.BigInteger, nullable=False, server_default='0')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('idx_users_username', func.lower(cls.username), unique=True),
                db.Index('idx_users_email', func.lower(cls.email)))

    def __init__(self, username, passhash, email, id=None, enabled=None, locked=None,
                 user_class=None, inviter_id=None, invites=None, uploaded=None,
                 downloaded=None):
        self.id = id
        self.username = username
        self.passhash = passhash
        self.email = email
        self.enabled = enabled
        self.locked = locked
        self.user_class = user_class
        inviter_id = inviter_id
        invites = invites

    @classmethod
    def from_id(cls, id):
        user = cls.from_cache(cls.__cache_key__.format(id=id))
        if not user:
            user = cls.query.get(id)
            cache.cache_model(user, timeout=3600 * 24 * 7)
        return user

    @classmethod
    def from_username(cls, username):
        username = username.lower()
        user = cls.query.filter(func.lower(cls.username) == username).one_or_none()
        if user:
            cache.cache_model(user, timeout=3600 * 24 * 7)
        return user

    @classmethod
    def register(cls, username, password, email):
        """
        Alternative constructor which generates a password hash and
        lowercases and strips leading and trailing spaces from the email.
        """
        return cls(
            username=username,
            passhash=generate_password_hash(password),
            email=email.lower().strip(),
            )

    @property
    def cache_key(self):
        return self.__cache_key__.format(id=self.id)

    @property
    def secondary_classes(self):
        return [sc.name for sc in self.secondary_class_models]

    @property
    def secondary_class_models(self):
        from pulsar.permissions.models import SecondaryClass, secondary_class_assoc_table as sat
        cache_key = self.__cache_key_secondary_classes__.format(id=self.id)
        secondary_class_names = cache.get(cache_key)
        if not secondary_class_names:
            secondary_class_names = [s[0] for s in db.session.execute(select(
                    [sat.c.secondary_user_class]
                    ).where(sat.c.user_id == self.id))]
            cache.set(cache_key, secondary_class_names, timeout=3600 * 24 * 28)

        secondary_classes = []
        for name in secondary_class_names:
            secondary_classes.append(SecondaryClass.from_name(name))
        return secondary_classes

    @property
    def inviter(self):
        return User.from_id(self.inviter_id) if self.inviter_id else None

    @property
    def api_keys(self):
        from pulsar.auth.models import APIKey
        return APIKey.from_user(self.id)

    @property
    def sessions(self):
        from pulsar.auth.models import Session
        return Session.from_user(self.id)

    @property
    def permissions(self):
        from pulsar.permissions.models import UserClass, UserPermission
        if self.locked:  # Locked accounts have restricted permissions.
            return app.config['LOCKED_ACCOUNT_PERMISSIONS']

        cache_key = self.__cache_key_permissions__.format(id=self.id)
        permissions = cache.get(cache_key)
        if not permissions:
            permissions = (db.session.query(UserClass.permissions)
                           .filter(UserClass.name == self.user_class)
                           .all()[0][0] or [])

            for secondary in self.secondary_class_models:
                permissions += secondary.permissions or []
            permissions = list(set(permissions))  # De-dupe

            user_permissions = (
                db.session.query(UserPermission.permission, UserPermission.granted)
                .filter(UserPermission.user_id == self.id).all())

            for up in user_permissions:
                if up[1] is False and up[0] in permissions:
                    permissions.remove(up[0])
                if up[1] is True and up[0] not in permissions:
                    permissions.append(up[0])

            cache.set(cache_key, permissions, timeout=3600 * 24 * 28)
        return permissions

    def set_password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

    def has_permission(self, permission):
        return permission in self.permissions
