import secrets
import pulsar.users.models  # noqa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import INET, ARRAY
from werkzeug.security import generate_password_hash, check_password_hash
from pulsar import db, cache


class Session(db.Model):
    __tablename__ = 'sessions'
    __cache_key__ = 'sessions_{hash}'
    __cache_key_of_user__ = 'sessions_user_{user_id}'
    __serializable_attrs__ = ('hash', 'user_id', 'persistent', 'last_used', 'ip',
                              'user_agent', 'active')

    hash = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    persistent = db.Column(db.Boolean, nullable=False, server_default='f')
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    csrf_token = db.Column(db.String(24), nullable=False)
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')

    @classmethod
    def generate_session(cls, user_id, ip, user_agent, persistent=False):
        """
        Create a new session with randomly generated secret keys and the
        user details passed in as params.

        :param int user_id: Session will belong to this user
        :param str ip: IP the session was created with
        :param str user_agent: User Agent the session was created with
        :param bool persistent: Whether or not to persist the session

        :return: A ``Session`` object
        """
        while True:
            hash = secrets.token_hex(5)
            if not cls.from_hash(hash):
                break
        csrf_token = secrets.token_hex(12)
        session = cls(
            user_id=user_id,
            hash=hash,
            csrf_token=csrf_token,
            ip=ip,
            user_agent=user_agent,
            persistent=persistent)

        db.session.add(session)
        db.session.commit()

        cache.cache_model(session)
        cache.delete(cls.__cache_key_of_user__.format(user_id=user_id))
        return session

    @classmethod
    def from_hash(cls, hash, include_dead=False):
        """
        Get a session from it's hash.

        :param str hash: The hash of the session
        :param bool include_dead: (Default ``False``) Whether or not to
            include dead sessions in the search

        :return: A ``Session`` object or ``None``
        """
        session = cls.from_cache(
            key=cls.__cache_key__.format(hash=hash),
            query=cls.query.filter(cls.hash == hash))

        if session and (include_dead or session.active):
            return session
        return None

    @classmethod
    def from_user(cls, user_id, include_dead=False):
        """
        Get all sessions owned by a user.

        :param int user_id: The User ID of the owner.
        :param bool include_dead: (Default ``False``) Whether or not to
            include dead API keys in the search

        :return: A ``list`` of ``APIKey`` objects
        """
        cache_key = cls.__cache_key_of_user__.format(user_id=user_id)
        session_hashes = cache.get(cache_key)
        if not session_hashes:
            session_hashes = [
                k[0] for k in db.session.query(cls.hash).filter(
                    cls.user_id == user_id).all()]
            cache.set(cache_key, session_hashes, timeout=3600 * 24 * 28)

        sessions = []
        for hash in session_hashes:
            sessions.append(cls.from_hash(hash, include_dead=True))

        return [s for s in sessions if s and (include_dead or s.active)]

    @property
    def cache_key(self):
        return self.__cache_key__.format(hash=self.hash)

    @staticmethod
    def expire_all_of_user(user_id):
        """
        Expire all active sessions that belong to a user.

        :param int user_id: The expired sessions belong to this user
        """
        hashes = db.session.query(Session.hash).filter(Session.active == 't').all()
        for hash in hashes:
            cache.delete(Session.__cache_key__.format(hash=hash[0]))

        db.session.query(Session).filter(
            Session.user_id == user_id
            ).update({'active': False})


class APIKey(db.Model):
    __tablename__ = 'api_keys'
    __cache_key__ = 'api_keys_{hash}'
    __cache_key_of_user__ = 'api_keys_user_{user_id}'
    __serializable_attrs__ = ('hash', 'user_id', 'last_used', 'ip', 'user_agent',
                              'active', 'permissions')

    hash = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    keyhashsalt = db.Column(db.String(128))
    last_used = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    user_agent = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')
    permissions = db.Column(ARRAY(db.String(32)))

    @classmethod
    def generate_key(cls, user_id, ip, user_agent, permissions=[]):
        """
        Create a new API Key with randomly generated secret keys and the
        user details passed in as params.

        :param int user_id: Session will belong to this user
        :param str ip: IP the session was created with
        :param str user_agent: User Agent the session was created with

        :return: An ``APIKey`` object
        """
        while True:
            hash = secrets.token_hex(5)
            if not cls.from_hash(hash, include_dead=True):
                break
        key = secrets.token_hex(8)
        api_key = cls(
            user_id=user_id,
            hash=hash,
            keyhashsalt=generate_password_hash(key),
            ip=ip,
            user_agent=user_agent,
            permissions=permissions,
            )
        db.session.add(api_key)
        db.session.commit()

        cache.cache_model(api_key)
        cache.delete(cls.__cache_key_of_user__.format(user_id=user_id))
        return (hash + key, api_key)

    @classmethod
    def from_hash(cls, hash, include_dead=False):
        """
        Get an API key from it's hash.

        :param str hash: The hash of the API key
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            API keys in the search

        :return: An ``APIKey`` object or ``None``
        """
        api_key = cls.from_cache(
            key=cls.__cache_key__.format(hash=hash),
            query=cls.query.filter(cls.hash == hash))

        if api_key and (include_dead or api_key.active):
            return api_key
        return None

    @classmethod
    def from_user(cls, user_id, include_dead=False):
        """
        Get all API keys owned by a user.

        :param int user_id: The User ID of the owner.
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            API keys in the search

        :return: A ``list`` of ``APIKey`` objects
        """
        api_key_hashes = cache.get(cls.__cache_key_of_user__.format(user_id=user_id))
        if not api_key_hashes:
            api_key_hashes = [
                k[0] for k in db.session.query(cls.hash).filter(cls.user_id == user_id).all()]
            cache.set(cls.__cache_key_of_user__.format(user_id=user_id),
                      api_key_hashes, timeout=3600 * 24 * 28)

        api_keys = []
        for hash in api_key_hashes:
            api_keys.append(cls.from_hash(hash, include_dead=True))

        return [k for k in api_keys if k and (include_dead or k.active)]

    @property
    def cache_key(self):
        return self.__cache_key__.format(hash=self.hash)

    def check_key(self, key):
        """
        Validates the authenticity of an API key against its stored hash.

        :param str key: The key to check against the hash
        :return: ``True`` if it matches, ``False`` if it doesn't
        """
        return check_password_hash(self.keyhashsalt, key)

    def has_permission(self, permission):
        """
        Checks if the API key is assigned a permission. If the API key
        is not assigned any permissions, it checks against the user's
        permissions instead.

        :param str permission: Permission to search for
        :return: ``True`` if permission is present, ``False`` if not
        """
        if self.permissions:
            return permission in self.permissions

        from pulsar.users.models import User
        user = User.from_id(self.user_id)
        return permission in user.permissions

    @staticmethod
    def revoke_all_of_user(user_id):
        """
        Revokes all active API keys of a user.

        :param int user_id: API keys of this user will be revoked
        """
        hashes = db.session.query(APIKey.hash).filter(APIKey.active == 't').all()
        for hash in hashes:
            cache.delete(APIKey.__cache_key__.format(hash=hash[0]))

        db.session.query(APIKey).filter(
            APIKey.user_id == user_id
            ).update({'active': False})
