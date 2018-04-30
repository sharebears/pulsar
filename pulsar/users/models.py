import pulsar.invites.models  # noqa
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, and_
from sqlalchemy.ext.declarative import declared_attr
from pulsar import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    invites = db.Column(db.Integer, nullable=False, server_default='0')

    sessions = relationship('Session', back_populates='user')
    api_keys = relationship('APIKey', back_populates='user')
    permissions = relationship('UserPermission')

    inviter = relationship('User', uselist=False)
    invites_sent = relationship(
        'Invite', back_populates='inviter', foreign_keys='Invite.inviter_id')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('idx_users_username', func.lower(cls.username), unique=True),
                db.Index('idx_users_email', func.lower(cls.email)))

    def __init__(self, username, password, email):
        self.username = username
        self.passhash = generate_password_hash(password)
        self.email = email.lower().strip()

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
        return db.session.query(UserPermission).filter(and_(
            (UserPermission.user_id == self.id),
            (UserPermission.permission == permission),
            )).one_or_none()


class UserPermission(db.Model):
    __tablename__ = 'users_permissions'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    permission = db.Column(db.String(32), primary_key=True)
