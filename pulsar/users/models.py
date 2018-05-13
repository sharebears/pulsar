import flask
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.sql import select
from sqlalchemy.ext.declarative import declared_attr
from pulsar import db, cache

app = flask.current_app


class User(db.Model):
    __tablename__ = 'users'
    __cache_key__ = 'users_{id}'
    __cache_key_permissions__ = 'users_{id}_permissions'
    __cache_key_secondary_classes__ = 'users_{id}_secondary_classes'

    __serialize__ = ('id', 'username', 'enabled', 'user_class', 'secondary_classes',
                     'uploaded', 'downloaded')
    __serialize_self__ = ('email', 'locked', 'invites', 'sessions', 'api_keys')
    __serialize_detailed__ = ('email', 'locked', 'invites', 'inviter', 'sessions', 'api_keys')
    __serialize_nested_exclude__ = ('inviter', 'sessions', 'api_keys')

    __permission_detailed__ = 'moderate_users'
    __permission_very_detailed__ = 'moderate_users_advanced'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, server_default='t')
    locked = db.Column(db.Boolean, nullable=False, server_default='f')
    user_class_id = db.Column(db.Integer, db.ForeignKey('user_classes.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    invites = db.Column(db.Integer, nullable=False, server_default='0')

    uploaded = db.Column(db.BigInteger, nullable=False, server_default='5368709120')  # 5 GB
    downloaded = db.Column(db.BigInteger, nullable=False, server_default='0')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('idx_users_username', func.lower(cls.username), unique=True),
                db.Index('idx_users_email', func.lower(cls.email)))

    @classmethod
    def from_username(cls, username):
        username = username.lower()
        user = cls.query.filter(func.lower(cls.username) == username).first()
        cache.cache_model(user)
        return user

    @classmethod
    def register(cls, username, password, email):
        """
        Alternative constructor which generates a password hash and
        lowercases and strips leading and trailing spaces from the email.
        """
        return super().new(
            username=username,
            passhash=generate_password_hash(password),
            email=email.lower().strip())

    @property
    def secondary_classes(self):
        return [sc.name for sc in self.secondary_class_models]

    @property
    def secondary_class_models(self):
        from pulsar.models import SecondaryClass, secondary_class_assoc_table as sat
        cache_key = self.__cache_key_secondary_classes__.format(id=self.id)
        secondary_class_ids = cache.get(cache_key)
        if not secondary_class_ids:
            secondary_class_ids = [s[0] for s in db.session.execute(select(
                    [sat.c.secondary_user_class]).where(sat.c.user_id == self.id))]
            cache.set(cache_key, secondary_class_ids)
        return [SecondaryClass.from_name(name) for name in secondary_class_ids]

    @property
    def inviter(self):
        return User.from_id(self.inviter_id) if self.inviter_id else None

    @property
    def api_keys(self):
        from pulsar.models import APIKey
        return APIKey.from_user(self.id)

    @property
    def sessions(self):
        from pulsar.models import Session
        return Session.from_user(self.id)

    @property
    def permissions(self):
        from pulsar.models import UserPermission
        if self.locked:  # Locked accounts have restricted permissions.
            return app.config['LOCKED_ACCOUNT_PERMISSIONS']

        cache_key = self.__cache_key_permissions__.format(id=self.id)
        permissions = cache.get(cache_key)
        if not permissions:
            permissions = self.user_class.permissions

            for secondary in self.secondary_class_models:
                permissions += secondary.permissions or []
            permissions = list(set(permissions))  # De-dupe

            user_permissions = (db.session.query(
                UserPermission.permission, UserPermission.granted)
                .filter(UserPermission.user_id == self.id).all())

            for up in user_permissions:
                if up[1] is False and up[0] in permissions:
                    permissions.remove(up[0])
                if up[1] is True and up[0] not in permissions:
                    permissions.append(up[0])

            cache.set(cache_key, permissions)
        return permissions

    def belongs_to_user(self):
        return flask.g.user and self.id == flask.g.user.id

    def set_password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

    def has_permission(self, permission):
        return permission and permission in self.permissions
