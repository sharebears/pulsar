import pulsar.invites.models  # noqa
import pulsar.permissions.models  # noqa
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from pulsar import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, server_default='t')
    user_class = db.Column(db.String, db.ForeignKey('user_classes.user_class'),
                           nullable=False, server_default='User')
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    invites = db.Column(db.Integer, nullable=False, server_default='0')

    sessions = relationship('Session', back_populates='user')
    api_keys = relationship('APIKey', back_populates='user')
    user_class_obj = relationship('UserClass')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('idx_users_username', func.lower(cls.username), unique=True),
                db.Index('idx_users_email', func.lower(cls.email)))

    def __init__(self, username, password, email):
        self.username = username
        self.passhash = generate_password_hash(password)
        self.email = email.lower().strip()

    @hybrid_property
    def permissions(self):
        from pulsar.permissions.models import UserClass, UserPermission
        permissions = (
            db.session.query(UserClass.permissions)
            .filter(UserClass.user_class == self.user_class)
            .all()[0][0] or [])

        user_permissions = (
            db.session.query(UserPermission.permission, UserPermission.granted)
            .filter(UserPermission.user_id == self.id).all())

        for up in user_permissions:
            if up[1] is False and up[0] in permissions:
                permissions.remove(up[0])
            if up[1] is True and up[0] not in permissions:
                permissions.append(up[0])

        return permissions

    @classmethod
    def from_id(cls, id):
        return cls.query.get(id)

    @classmethod
    def from_username(cls, username):
        username = username.lower()
        return cls.query.filter(func.lower(cls.username) == username).one_or_none()

    def set_password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

    def has_permission(self, permission):
        return permission in self.permissions
