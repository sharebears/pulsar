from typing import List, Optional, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr

from pulsar import APIException, db
from pulsar.mixins.model import ModelMixin

UC = TypeVar('UC', bound='ClassMixin')


class ClassMixin(ModelMixin):
    __serialize__ = (
        'id',
        'name', )
    __serialize_detailed__ = (
        'permissions',
        'forum_permissions', )

    __permission_detailed__ = 'modify_user_classes'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(24), nullable=False)
    permissions: List[str] = db.Column(ARRAY(db.String(36)), nullable=False, server_default='{}')
    forum_permissions: List[str] = db.Column(  # noqa TODO: Why E701?
        ARRAY(db.String(36)), nullable=False, server_default='{}')

    @declared_attr
    def __table_args__(cls):
        return db.Index(f'ix_{cls.__tablename__}_name', func.lower(cls.name), unique=True),

    @classmethod
    def from_name(cls: Type[UC],
                  name: str) -> Optional[UC]:
        name = name.lower()
        return cls.query.filter(func.lower(cls.name) == name).scalar()

    @classmethod
    def new(cls: Type[UC],
            name: str,
            permissions: List[str] = None) -> UC:
        if cls.from_name(name):
            raise APIException(f'Another {cls.__name__} already has the name {name}.')
        return super()._new(
            name=name,
            permissions=permissions or [])

    @classmethod
    def get_all(cls: Type[UC]) -> List[UC]:
        return cls.get_many(key=cls.__cache_key_all__)
