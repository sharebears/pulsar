from sqlalchemy import func, and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import ARRAY
from pulsar import db


class UserPermission(db.Model):
    __tablename__ = 'users_permissions'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    permission = db.Column(db.String(32), primary_key=True)
    granted = db.Column(db.Boolean, nullable=False, server_default='t')

    @classmethod
    def from_attrs(cls, user_id, permission):
        return cls.query.filter(and_(
            (cls.user_id == user_id),
            (cls.permission == permission),
            )).one_or_none()

    @classmethod
    def from_user(cls, user_id):
        """
        Gets a dict of all custom permissions assigned to a user.

        :param int user_id: User ID the permissions belong to

        :return: A ``dict`` of permissions with a permission ``str`` as the key
            and a granted ``boolean`` as the value.
        """
        permissions = cls.query.filter(cls.user_id == user_id).all()
        response = {}
        for perm in permissions:
            response[perm.permission] = perm.granted
        return response


class UserClass(db.Model):
    __tablename__ = 'user_classes'

    user_class = db.Column(db.String(24), primary_key=True)
    permissions = db.Column(ARRAY(db.String(32)))

    @declared_attr
    def __table_args__(cls):
        return (
            db.Index('idx_user_classes_name', func.lower(cls.user_class), unique=True),
            )

    @classmethod
    def from_name(cls, user_class):
        user_class = user_class.lower()
        return cls.query.filter(func.lower(cls.user_class) == user_class).first()

    @classmethod
    def get_all(cls):
        return cls.query.all()
