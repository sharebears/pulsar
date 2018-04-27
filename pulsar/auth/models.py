import secrets
import pulsar.users.models  # noqa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, and_
from sqlalchemy.dialects import postgresql
from werkzeug.security import generate_password_hash, check_password_hash
from pulsar import db


class Session(db.Model):
    __tablename__ = 'sessions'

    hash = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(postgresql.INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    csrf_token = db.Column(db.String(24), nullable=False)
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')

    user = relationship('User', back_populates='sessions', uselist=False, lazy=False)

    @classmethod
    def generate_session(cls, user_id, ip):
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
            )

    @classmethod
    def from_hash(cls, hash, include_dead=False):
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
    ip = db.Column(postgresql.INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')

    user = relationship('User', back_populates='api_keys', uselist=False, lazy=False)
    permissions = relationship('APIPermission')

    @classmethod
    def generate_key(cls, user_id, ip):
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
            ))

    @classmethod
    def from_hash(cls, hash, include_dead=False):
        query = cls.query.filter(cls.hash == hash)
        if not include_dead:
            query = query.filter(cls.active == 't')
        return query.one_or_none()

    def check_key(self, key):
        return check_password_hash(self.keyhashsalt, key)

    def has_permission(self, permission):
        return db.session.query(APIPermission).filter(and_(
            (APIPermission.api_key_hash == self.hash),
            (APIPermission.permission == permission),
            )).one_or_none()

    @staticmethod
    def revoke_all_of_user(user_id):
        db.session.query(APIKey).filter(
            APIKey.user_id == user_id
            ).update({'active': False})


class APIPermission(db.Model):
    __tablename__ = 'api_permissions'

    api_key_hash = db.Column(
        db.String(10), db.ForeignKey('api_keys.hash'), primary_key=True)
    permission = db.Column(db.String(32), primary_key=True)
