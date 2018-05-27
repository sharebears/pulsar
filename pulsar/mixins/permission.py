from typing import Dict

from sqlalchemy.ext.declarative import declared_attr

from pulsar import db
from pulsar.mixins.multi_pk import MultiPKMixin


class PermissionMixin(MultiPKMixin):
    permission: str = db.Column(db.String(36), primary_key=True)
    granted: bool = db.Column(db.Boolean, nullable=False, server_default='t')

    @declared_attr
    def user_id(cls) -> int:
        return db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    @classmethod
    def from_user(cls, user_id: int) -> Dict[str, bool]:
        """
        Gets a dict of all custom permissions assigned to a user.

        :param user_id: User ID the permissions belong to

        :return:        Dict of permissions with the name as the
                        key and the ``granted`` value as the value
        """
        return {p.permission: p.granted for p in cls.query.filter(  # type: ignore
                    cls.user_id == user_id).all()}
