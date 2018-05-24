from typing import List

from sqlalchemy import and_, select

from pulsar import db
from pulsar.mixins import ClassMixin, PermissionMixin
from pulsar.users.models import User


class UserClass(db.Model, ClassMixin):
    __tablename__ = 'user_classes'
    __cache_key__ = 'user_class_{id}'
    __cache_key_all__ = 'user_classes'

    def has_users(self) -> bool:
        return bool(User.query.filter(User.user_class_id == self.id).first())


class SecondaryClass(db.Model, ClassMixin):
    __tablename__ = 'secondary_classes'
    __cache_key__ = 'secondary_class_{id}'
    __cache_key_all__ = 'secondary_classes'
    __cache_key_of_user__ = 'secondary_classes_users_{id}'

    @classmethod
    def from_user(cls, user_id: int) -> List['SecondaryClass']:
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(id=user_id),
            expr_override=select(
                [secondary_class_assoc_table.c.secondary_class_id]).where(
                    secondary_class_assoc_table.c.user_id == user_id))

    def has_users(self) -> bool:
        return bool(db.session.execute(
            select([secondary_class_assoc_table.c.user_id]).where(
                secondary_class_assoc_table.c.secondary_class_id == self.id).limit(1)))


secondary_class_assoc_table = db.Table(
    'secondary_class_assoc', db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
    db.Column('secondary_class_id', db.Integer, db.ForeignKey('secondary_classes.id'),
              nullable=False))


class UserPermission(db.Model, PermissionMixin):
    __tablename__ = 'users_permissions'


class ForumPermission(db.Model, PermissionMixin):
    __tablename__ = 'forums_permissions'
    # TODO: Cache key

    @classmethod
    def get_ungranted_from_user(cls, user_id):
        return {p.permission for p in cls.query.filter(and_(
            (cls.user_id == user_id),
            (cls.granted == 'f'))).all()}
