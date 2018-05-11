from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import ARRAY
from pulsar import db, cache


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
    __cache_key__ = 'user_class_{name}'
    __cache_key_all__ = 'user_classes'
    __serializable_attrs__ = ('name', )
    __serializable_attrs_very_detailed__ = ('permissions', )

    name = db.Column(db.String(24), primary_key=True)
    permissions = db.Column(ARRAY(db.String(32)))

    @classmethod
    def from_name(cls, name):
        name = name.lower()
        user_class = cls.from_cache(cls.__cache_key__.format(name=name))
        if not user_class:
            user_class = cls.query.filter(func.lower(cls.name) == name).first()
            cache.cache_model(user_class, timeout=3600 * 24 * 28)
        return user_class

    @classmethod
    def get_all(cls):
        cache_key = cls.__cache_key_all__
        user_class_names = cache.get(cache_key)
        if not user_class_names:
            user_class_names = [uc[0] for uc in db.session.query(cls.name).all()]
            cache.set(cache_key, user_class_names, timeout=3600 * 24 * 28)

        user_classes = []
        for user_class_name in user_class_names:
            user_classes.append(cls.from_name(user_class_name))
        return user_classes

    @property
    def cache_key(self):
        return self.__cache_key__.format(name=self.name)


secondary_class_assoc_table = db.Table(
    'secondary_class_assoc', db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('secondary_user_class', db.String(24),
              db.ForeignKey('secondary_classes.name')),
    )


class SecondaryClass(db.Model):
    __tablename__ = 'secondary_classes'
    __cache_key__ = 'secondary_class_{name}'
    __cache_key_all__ = 'secondary_classes'
    __cache_key_users__ = 'secondary_class_users_{name}'
    __serializable_attrs__ = ('name', )
    __serializable_attrs_very_detailed__ = ('permissions', )

    name = db.Column(db.String(24), primary_key=True)
    permissions = db.Column(ARRAY(db.String(32)))

    @classmethod
    def from_name(cls, name):
        name = name.lower()
        user_class = cls.from_cache(cls.__cache_key__.format(name=name))
        if not user_class:
            user_class = cls.query.filter(func.lower(cls.name) == name).first()
            cache.cache_model(user_class, timeout=3600 * 24 * 28)
        return user_class

    @classmethod
    def get_all(cls):
        cache_key = cls.__cache_key_all__
        user_class_names = cache.get(cache_key)
        if not user_class_names:
            user_class_names = [uc[0] for uc in db.session.query(cls.name).all()]
            cache.set(cache_key, user_class_names, timeout=3600 * 24 * 28)

        user_classes = []
        for user_class_name in user_class_names:
            user_classes.append(cls.from_name(user_class_name))
        return user_classes

    @property
    def cache_key(self):
        return self.__cache_key__.format(name=self.name)
