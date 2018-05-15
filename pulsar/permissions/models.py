from sqlalchemy import and_, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import select

from pulsar import APIException, db


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
    __cache_key__ = 'user_class_{id}'
    __cache_key_all__ = 'user_classes'

    __serialize__ = ('id', 'name', )
    __serialize_detailed__ = ('permissions', )

    __permission_detailed__ = 'modify_user_classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), nullable=False)
    permissions = db.Column(ARRAY(db.String(32)))

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_user_classes_name', func.lower(cls.name), unique=True), )

    @classmethod
    def from_name(cls, name):
        name = name.lower()
        return cls.query.filter(func.lower(cls.name) == name).first()

    def has_users(self):
        from pulsar.models import User
        return User.query.filter(User.user_class_id == self.id).limit(1).first()

    @classmethod
    def new(cls, name, permissions=None):
        if cls.from_name(name):
            raise APIException(f'Another user class already has the name {name}.')
        return super().new(
            name=name,
            permissions=permissions)

    @classmethod
    def get_all(cls):
        return cls.get_many(key=cls.__cache_key_all__)


secondary_class_assoc_table = db.Table(
    'secondary_class_assoc', db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('secondary_class_id', db.Integer, db.ForeignKey('secondary_classes.id'),
              nullable=False))


class SecondaryClass(db.Model):
    __tablename__ = 'secondary_classes'
    __cache_key__ = 'secondary_class_{id}'
    __cache_key_all__ = 'secondary_classes'
    __cache_key_of_user__ = 'secondary_classes_users_{id}'

    __serialize__ = ('id', 'name', )
    __serialize_detailed__ = ('permissions', )

    __permission_detailed__ = 'modify_user_classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), nullable=False)
    permissions = db.Column(ARRAY(db.String(32)))

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_secondary_classes_name', func.lower(cls.name), unique=True), )

    @classmethod
    def from_name(cls, name):
        name = name.lower()
        return cls.query.filter(func.lower(cls.name) == name).first()

    @classmethod
    def from_user(cls, user_id):
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(id=user_id),
            expr_override=select(
                [secondary_class_assoc_table.c.secondary_class_id]).where(
                    secondary_class_assoc_table.c.user_id == user_id))

    def has_users(self):
        return db.session.execute(
            select([secondary_class_assoc_table.c.user_id]).where(
                secondary_class_assoc_table.c.secondary_class_id == self.id).limit(1))

    @classmethod
    def new(cls, name, permissions=None):
        if cls.from_name(name):
            raise APIException(f'Another secondary class already has the name {name}.')
        return super().new(
            name=name,
            permissions=permissions)

    @classmethod
    def get_all(cls):
        return cls.get_many(key=cls.__cache_key_all__)
