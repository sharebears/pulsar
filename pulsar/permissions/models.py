from sqlalchemy import func, and_
from sqlalchemy.orm import relationship
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
    __serializable_attrs__ = ('name', )
    __serializable_attrs_very_detailed__ = ('permissions', )

    name = db.Column(db.String(24), primary_key=True)
    permissions = db.Column(ARRAY(db.String(32)))

    @classmethod
    def from_name(cls, name):
        name = name.lower()
        return cls.query.filter(func.lower(cls.name) == name).first()

    @classmethod
    def get_all(cls):
        return cls.query.all()


secondary_class_assoc_table = db.Table(
    'secondary_class_assoc', db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('secondary_user_class', db.String(24),
              db.ForeignKey('secondary_classes.name')),
    )


class SecondaryUserClass(db.Model):
    __tablename__ = 'secondary_classes'
    __serializable_attrs__ = ('name', )
    __serializable_attrs_very_detailed__ = ('permissions', )

    name = db.Column(db.String(24), primary_key=True)
    permissions = db.Column(ARRAY(db.String(32)))

    users = relationship(
        'User', secondary=secondary_class_assoc_table, back_populates='secondary_class_objs')

    @classmethod
    def from_name(cls, name):
        name = name.lower()
        return cls.query.filter(func.lower(cls.name) == name).first()

    @classmethod
    def get_all(cls):
        return cls.query.all()
