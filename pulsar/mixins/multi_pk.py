from typing import Any, List, Optional, Type, TypeVar, Union

from flask_sqlalchemy import BaseQuery, Model
from sqlalchemy import and_
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression

from pulsar import cache, db

MPK = TypeVar('MPK', bound='MultiPKMixin')


class MultiPKMixin(Model):
    """
    A model mixin for models with multiple primary keys, typically representative
    of many-to-many relational tables.
    """
    __cache_key__: Optional[str] = None
    __cache_key_all__: Optional[str] = None
    __deletion_attr__: Optional[str] = None

    __serialize__: tuple = ()
    __serialize_detailed__: tuple = ()
    __serialize_very_detailed__: tuple = ()
    __serialize_nested_include__: tuple = ()
    __serialize_nested_exclude__: tuple = ()

    __permission_detailed__: Optional[str] = None
    __permission_very_detailed__: Optional[str] = None

    @classmethod
    def from_attrs(cls: Type[MPK], **kwargs: Union[str, int]) -> Optional[MPK]:
        """
        Get an instance of the model from its attributes.
        """
        return cls.query.filter(and_(*(
            getattr(cls, k) == v for k, v in kwargs.items()))).scalar()

    @classmethod
    def get_col_from_many(cls,
                          *,
                          column: InstrumentedAttribute,
                          key: str = None,
                          filter: BinaryExpression = None,
                          order: BinaryExpression = None) -> List[int]:
        values = cache.get(key) if key else None
        if values is None:
            query = cls._construct_query(db.session.query(column), filter, order)
            values = [x[0] for x in query.all()]
            cache.set(key, values)
        return values

    @classmethod
    def _new(cls: Type[MPK],
             **kwargs: Any) -> MPK:
        """
        Create a new instance of the model, add it to the instance, and return it.

        :param kwargs: The new attributes of the model
        """
        model = cls(**kwargs)
        db.session.add(model)
        db.session.commit()
        return model

    @staticmethod
    def _construct_query(query: BaseQuery,
                         filter: BinaryExpression = None,
                         order: BinaryExpression = None) -> BaseQuery:
        """
        A convenience function to save code space for query generations. Takes filters
        and order_bys and applies them to the query, returning a query ready to be ran.

        :param query:  A query that can be built upon
        :param filter: A SQLAlchemy query filter expression
        :param order:  A SQLAlchemy query order_by expression

        :return:       A Flask-SQLAlchemy ``BaseQuery``
        """
        if filter is not None:
            query = query.filter(filter)
        if order is not None:
            query = query.order_by(order)
        return query
