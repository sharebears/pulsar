from datetime import datetime
from typing import List, Optional, Union

import flask
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import BinaryExpression

from pulsar import APIException, _403Exception, cache, db
from pulsar.mixins import MultiPKMixin, SinglePKMixin
from pulsar.permissions.models import ForumPermission
from pulsar.users.models import User
from pulsar.utils import cached_property

app = flask.current_app


class ForumCategory(db.Model, SinglePKMixin):
    __tablename__ = 'forums_categories'
    __cache_key__ = 'forums_categories_{id}'
    __cache_key_all__ = 'forums_categories_all'
    __deletion_attr__ = 'deleted'

    __serialize__ = (
        'id',
        'name',
        'description',
        'position',
        'forums')
    __serialize_very_detailed__ = (
        'deleted', )
    __serialize_nested_exclude__ = (
        'forums', )

    __permission_very_detailed__ = 'modify_forums'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(32), nullable=False)
    description: Optional[str] = db.Column(db.Text)
    position: int = db.Column(db.SmallInteger, nullable=False, server_default='0', index=True)
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f', index=True)

    @classmethod
    def get_all(cls, include_dead: bool = False) -> List['ForumCategory']:
        return cls.get_many(
            key=cls.__cache_key_all__,
            order=cls.position.asc(),  # type: ignore
            include_dead=include_dead,
            required_properties=('forums', ))

    @classmethod
    def new(cls,
            name: str,
            description: str = None,
            position: int = 0) -> 'ForumCategory':
        return super()._new(
            name=name,
            description=description,
            position=position)

    @cached_property
    def forums(self) -> List['Forum']:
        return Forum.from_category(self.id)


class Forum(db.Model, SinglePKMixin):
    __tablename__ = 'forums'
    __cache_key__ = 'forums_{id}'
    __cache_key_last_updated__ = 'forums_{id}_last_updated'
    __cache_key_thread_count__ = 'forums_{id}_thread_count'
    __cache_key_of_category__ = 'forums_forums_of_categories_{id}'
    __permission_key__ = 'forums_forums_permission_{id}'
    __deletion_attr__ = 'deleted'

    __serialize__ = (
        'id',
        'name',
        'description',
        'category',
        'position',
        'thread_count',
        'threads')
    __serialize_very_detailed__ = (
        'deleted', )
    __serialize_nested_include__ = (
        'last_updated_thread', )
    __serialize_nested_exclude__ = (
        'category',
        'threads')

    __permission_very_detailed__ = 'modify_forums'

    _threads: List['ForumThread']

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(32), nullable=False)
    description: Optional[str] = db.Column(db.Text)
    category_id: int = db.Column(
        db.Integer, db.ForeignKey('forums_categories.id'), nullable=False, index=True)
    position: int = db.Column(db.SmallInteger, nullable=False, server_default='0', index=True)
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f', index=True)

    @classmethod
    def from_category(cls, category_id: int) -> List['Forum']:
        return cls.get_many(
            key=cls.__cache_key_of_category__.format(id=category_id),
            filter=cls.category_id == category_id,
            order=cls.position.asc())  # type: ignore

    @classmethod
    def new(cls,
            name: str,
            category_id: int,
            description: str = None,
            position: int = 0) -> Optional['Forum']:
        ForumCategory.is_valid(category_id, error=True)
        cache.delete(cls.__cache_key_of_category__.format(id=category_id))
        return super()._new(
            name=name,
            category_id=category_id,
            description=description,
            position=position)

    @classmethod
    def from_subscribed_user(cls, user_id: int) -> List['Forum']:
        return cls.get_many(
            key=ForumSubscription.__cache_key_of_users__.format(user_id=user_id),
            filter=cls.id.in_(db.session.query(ForumSubscription.forum_id)  # type: ignore
                              .filter(ForumSubscription.user_id == user_id)),
            order=Forum.id.asc())  # type: ignore

    @cached_property
    def category(self) -> 'ForumCategory':
        return ForumCategory.from_pk(self.category_id)

    @cached_property
    def thread_count(self) -> 'int':
        return self.count(
            key=self.__cache_key_thread_count__.format(id=self.id),
            attribute=ForumThread.id,
            filter=and_(ForumThread.forum_id == self.id, ForumThread.deleted == 'f'))

    @cached_property
    def last_updated_thread(self) -> Optional['ForumThread']:
        return ForumThread.from_query(
            key=self.__cache_key_last_updated__.format(id=self.id),
            filter=(ForumThread.forum_id == self.id),
            order=ForumThread.last_updated.desc())

    @property
    def threads(self) -> List['ForumThread']:
        if not hasattr(self, '_threads'):
            self._threads = ForumThread.from_forum(self.id, 1, limit=50)
        return self._threads

    def set_threads(self,
                    page: int,
                    limit: int,
                    include_dead: bool = False) -> None:
        self._threads = ForumThread.from_forum(self.id, page, limit, include_dead)

    def can_access(self,
                   permission: str = None,
                   error: bool = False) -> bool:
        """Determines whether or not the user has the permissions to access the forum."""
        if flask.g.user is None:  # pragma: no cover
            if error:
                raise _403Exception
            return False

        # Explicit forum access
        permission_key = self.__permission_key__.format(id=self.id)
        if (flask.g.user.has_permission(permission_key)
                or (permission is not None and flask.g.user.has_permission(permission))):
            return True

        # If user has access to a thread in the forum, they can view the metadata of the forum
        # (albeit they can't view threads beyond their alloted ones).
        forum_thread_permissions = {
            ForumThread.__permission_key__.format(id=fid)
            for fid in ForumThread.get_ids_from_forum(self.id)}
        if any(fperm in forum_thread_permissions for fperm in flask.g.user.forum_permissions):
            return True
        if error:
            raise _403Exception
        return False


class ForumThread(db.Model, SinglePKMixin):
    __tablename__ = 'forums_threads'
    __cache_key__ = 'forums_threads_{id}'
    __cache_key_post_count__ = 'forums_threads_{id}_post_count'
    __cache_key_of_forum__ = 'forums_threads_forums_{id}'
    __cache_key_last_post__ = 'forums_threads_{id}_last_post'
    __permission_key__ = 'forums_threads_permission_{id}'
    __deletion_attr__ = 'deleted'

    __serialize__ = (
        'id',
        'topic',
        'forum',
        'poster',
        'locked',
        'sticky',
        'created_time',
        'poll',
        'last_post',
        'last_viewed_post',
        'subscribed',
        'post_count',
        'posts')
    __serialize_detailed__ = (
        'thread_notes', )
    __serialize_very_detailed__ = (
        'deleted', )
    __serialize_nested_exclude__ = (
        'poll',
        'forum',
        'posts')

    __permission_detailed__ = 'modify_forum_threads'
    __permission_very_detailed__ = 'modify_forum_threads_advanced'

    _posts: List['ForumPost']

    id: int = db.Column(db.Integer, primary_key=True)
    topic: str = db.Column(db.String(150), nullable=False)
    forum_id = db.Column(
        db.Integer, db.ForeignKey('forums.id'), nullable=False, index=True)  # type: int
    poster_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_time: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    locked: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f', index=True)

    @declared_attr
    def __table_args__(cls):
        return db.Index('ix_forums_threads_topic', func.lower(cls.topic)),

    @classmethod
    def from_forum(cls,
                   forum_id: int,
                   page: int = 1,
                   limit: Optional[int] = 50,
                   include_dead: bool = False) -> List['ForumThread']:
        return cls.get_many(
            key=cls.__cache_key_of_forum__.format(id=forum_id),
            filter=cls.forum_id == forum_id,
            order=cls.last_updated.desc(),
            page=page,
            limit=limit,
            include_dead=include_dead)

    @classmethod
    def new(cls,
            topic: str,
            forum_id: int,
            poster_id: int) -> Optional['ForumThread']:
        Forum.is_valid(forum_id, error=True)
        User.is_valid(poster_id, error=True)
        cache.delete(cls.__cache_key_of_forum__.format(id=forum_id))
        return super()._new(
            topic=topic,
            forum_id=forum_id,
            poster_id=poster_id)

    @classmethod
    def get_ids_from_forum(cls, id):
        return cls.get_pks_of_many(
            key=cls.__cache_key_of_forum__.format(id=id),
            filter=cls.forum_id == id,
            order=cls.last_updated.desc())

    @classmethod
    def from_subscribed_user(cls, user_id: int) -> List['ForumThread']:
        return cls.get_many(pks=cls.subscribed_ids(user_id))

    @classmethod
    def subscribed_ids(cls, user_id: int) -> List[Union[str, int]]:
        return cls.get_pks_of_many(
            key=ForumThreadSubscription.__cache_key_of_users__.format(user_id=user_id),
            filter=cls.id.in_(db.session.query(ForumThreadSubscription.thread_id)  # type: ignore
                              .filter(ForumThreadSubscription.user_id == user_id)),
            order=ForumThread.id.asc())  # type: ignore

    @classmethod
    def new_subscriptions(cls, user_id: int) -> List['ForumThread']:
        return cls.get_many(
            key=ForumThreadSubscription.__cache_key_active__.format(user_id=user_id),
            filter=and_(
                (cls.id.in_(db.session.query(ForumThreadSubscription.thread_id)  # type: ignore
                            .filter(ForumThreadSubscription.user_id == user_id))),
                or_((cls.last_post_id > db.session.query(
                    ForumLastViewedPost.post_id).filter(and_(
                        ForumLastViewedPost.user_id == user_id,
                        ForumLastViewedPost.thread_id == cls.id))),
                    (db.session.query(
                        ForumLastViewedPost.post_id).filter(and_(
                            ForumLastViewedPost.user_id == user_id,
                            ForumLastViewedPost.thread_id == cls.id)).as_scalar().is_(None)))
                ),
            order=cls.last_post_id.desc())

    @hybrid_property
    def last_updated(cls) -> BinaryExpression:
        return select([func.max(ForumPost.time)]).where(ForumPost.thread_id == cls.id).as_scalar()

    @hybrid_property
    def last_post_id(cls) -> BinaryExpression:
        return select([func.max(ForumPost.id)]).where(ForumPost.thread_id == cls.id).as_scalar()

    @cached_property
    def last_post(self) -> Optional['ForumPost']:
        return ForumPost.from_query(
            key=self.__cache_key_last_post__.format(id=self.id),
            filter=and_(
                ForumPost.thread_id == self.id,
                ForumPost.deleted == 'f'),
            order=ForumPost.id.desc())  # type: ignore

    @cached_property
    def last_viewed_post(self) -> Optional['ForumPost']:
        return ForumLastViewedPost.post_from_attrs(
            thread_id=self.id,
            user_id=flask.g.user.id) if flask.g.user else None

    @cached_property
    def forum(self) -> 'Forum':
        return Forum.from_pk(self.forum_id)

    @cached_property
    def poster(self) -> User:
        return User.from_pk(self.poster_id)

    @cached_property
    def poll(self) -> 'ForumPoll':
        return ForumPoll.from_thread(self.id)

    @cached_property
    def post_count(self) -> int:
        return self.count(
            key=self.__cache_key_post_count__.format(id=self.id),
            attribute=ForumPost.id,
            filter=and_(ForumPost.thread_id == self.id, ForumPost.deleted == 'f',))

    @cached_property
    def thread_notes(self) -> List['ForumThreadNote']:
        return ForumThreadNote.from_thread(self.id)

    @cached_property
    def subscribed(self) -> bool:
        return self.id in set(self.subscribed_ids(flask.g.user.id)) if flask.g.user else False

    @property
    def posts(self) -> List['ForumPost']:
        if not hasattr(self, '_posts'):
            self._posts = ForumPost.from_thread(self.id, 1, limit=50)
        return self._posts

    def set_posts(self,
                  page: int = 1,
                  limit: int = 50,
                  include_dead: bool = False) -> None:
        self._posts = ForumPost.from_thread(self.id, page, limit, include_dead)

    def can_access(self,
                   permission: str = None,
                   error: bool = False) -> bool:
        """Determines whether or not the user has the permissions to access the thread."""
        if flask.g.user is None:  # pragma: no cover
            if error:
                raise _403Exception
            return False

        # Explicit thread access
        permission_key = self.__permission_key__.format(id=self.id)
        if (flask.g.user.has_permission(permission_key)
                or (permission is not None and flask.g.user.has_permission(permission))):
            return True

        # Access to forum gives access to all threads by default.
        # If user has been ungranted the thread, they cannot view it regardless.
        ungranted_threads = ForumPermission.get_ungranted_from_user(flask.g.user.id)
        if permission_key not in ungranted_threads and (
                flask.g.user.has_permission(Forum.__permission_key__.format(id=self.forum_id))):
            return True
        if error:
            raise _403Exception
        return False


class ForumPost(db.Model, SinglePKMixin):
    __tablename__ = 'forums_posts'
    __cache_key__ = 'forums_posts_{id}'
    __cache_key_of_thread__ = 'forums_posts_threads_{id}'
    __deletion_attr__ = 'deleted'

    __serialize__ = (
        'id',
        'thread_id',
        'poster',
        'contents',
        'time',
        'edited_time',
        'sticky',
        'editor', )
    __serialize_very_detailed__ = (
        'deleted',
        'edit_history', )
    __serialize_nested_exclude__ = (
        'thread_id', )

    __permission_very_detailed__ = 'modify_forum_posts_advanced'

    id: int = db.Column(db.Integer, primary_key=True)
    thread_id: int = db.Column(
        db.Integer, db.ForeignKey('forums_threads.id'), nullable=False, index=True)
    poster_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    contents: str = db.Column(db.Text, nullable=False)
    time: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    sticky: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    edited_user_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('users.id'))
    edited_time: Optional[datetime] = db.Column(db.DateTime(timezone=True))
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f', index=True)

    @classmethod
    def from_thread(cls,
                    thread_id: int,
                    page: int = 1,
                    limit: int = 50,
                    include_dead: bool = False) -> List['ForumPost']:
        return cls.get_many(
            key=cls.__cache_key_of_thread__.format(id=thread_id),
            filter=cls.thread_id == thread_id,
            order=cls.id.asc(),  # type: ignore
            page=page,
            limit=limit,
            include_dead=include_dead)

    @classmethod
    def get_ids_from_thread(cls, id):
        return cls.get_pks_of_many(
            key=cls.__cache_key_of_thread__.format(id=id),
            filter=cls.thread_id == id,
            order=cls.id.asc())

    @classmethod
    def new(cls,
            thread_id: int,
            poster_id: int,
            contents: str) -> Optional['ForumPost']:
        ForumThread.is_valid(thread_id, error=True)
        User.is_valid(poster_id, error=True)
        cache.delete(cls.__cache_key_of_thread__.format(id=thread_id))
        return super()._new(
            thread_id=thread_id,
            poster_id=poster_id,
            contents=contents)

    @cached_property
    def poster(self) -> User:
        return User.from_pk(self.poster_id)

    @cached_property
    def editor(self) -> Optional[User]:
        return User.from_pk(self.edited_user_id)

    @cached_property
    def edit_history(self) -> List['ForumPostEditHistory']:
        return ForumPostEditHistory.from_post(self.id)


class ForumPostEditHistory(db.Model, SinglePKMixin):
    __tablename__ = 'forums_posts_edit_history'
    __cache_key__ = 'forums_posts_edit_history_{id}'
    __cache_key_of_post__ = 'forums_posts_edit_history_posts_{id}'

    __serialize_very_detailed__ = (
        'id',
        'editor',
        'contents',
        'time')

    __permission_very_detailed__ = 'modify_forum_posts_advanced'

    id: int = db.Column(db.Integer, primary_key=True)
    post_id: int = db.Column(db.Integer, db.ForeignKey('forums_posts.id'), nullable=False)
    editor_id: int = db.Column(db.Integer, db.ForeignKey('users.id'))
    contents: str = db.Column(db.Text, nullable=False)
    time: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @classmethod
    def from_post(cls, post_id: int) -> List['ForumPostEditHistory']:
        return cls.get_many(
            key=cls.__cache_key_of_post__.format(id=post_id),
            filter=cls.post_id == post_id,
            order=cls.id.desc())  # type: ignore

    @classmethod
    def new(cls,
            post_id: int,
            editor_id: int,
            contents: str,
            time: datetime) -> Optional[ForumPost]:
        ForumPost.is_valid(post_id, error=True)
        User.is_valid(editor_id, error=True)
        cache.delete(cls.__cache_key_of_post__.format(id=post_id))
        return super()._new(
            post_id=post_id,
            editor_id=editor_id,
            contents=contents,
            time=time)

    @cached_property
    def editor(self) -> User:
        return User.from_pk(self.editor_id)


class ForumLastViewedPost(db.Model):
    __tablename__ = 'last_viewed_forum_posts'
    __cache_key__ = 'last_viewed_forum_post_{thread_id}_{user_id}'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forums_posts.id'))

    @classmethod
    def post_from_attrs(cls, thread_id, user_id):
        cache_key = cls.__cache_key__.format(thread_id=thread_id, user_id=user_id)
        post_id = cache.get(cache_key)
        if not post_id:
            last_viewed = cls.query.filter(and_(
                (cls.thread_id == thread_id),
                (cls.user_id == user_id))).scalar()
            post_id = last_viewed.post_id if last_viewed else None
        post = ForumPost.from_pk(post_id, include_dead=True)
        if not post:
            return None
        if post.deleted:  # Get the last non-deleted and read post.
            post = ForumPost.from_query(
                filter=and_(
                    (ForumPost.thread_id == thread_id),
                    (ForumPost.id < post.id),
                    (ForumPost.deleted == 'f')),
                order=ForumPost.id.desc())  # type: ignore
        cache.set(cache_key, post.id if post else None)
        return post


class ForumSubscription(db.Model, MultiPKMixin):
    __tablename__ = 'forums_forums_subscriptions'
    __cache_key_users__ = 'forums_forums_subscriptions_{forum_id}_users'
    __cache_key_of_users__ = 'forums_forums_subscriptions_{user_id}'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id'), primary_key=True)

    @classmethod
    def new(cls,
            *,
            user_id: int,
            forum_id: int) -> Optional['ForumSubscription']:
        Forum.is_valid(forum_id, error=True)
        User.is_valid(user_id, error=True)
        return super()._new(
            user_id=user_id,
            forum_id=forum_id)

    @classmethod
    def user_ids_from_forum(cls, id: int) -> List[int]:
        cache_key = cls.__cache_key_users__.format(forum_id=id)
        user_ids = cache.get(cache_key)
        if not user_ids:
            user_ids = [
                i for i, in db.session.query(cls.user_id).filter(cls.forum_id == id).all()]
            cache.set(cache_key, user_ids)
        return user_ids


class ForumThreadSubscription(db.Model, MultiPKMixin):
    __tablename__ = 'forums_threads_subscriptions'
    __cache_key_active__ = 'forums_threads_subscriptions_active_{user_id}'
    __cache_key_users__ = 'forums_threads_subscriptions_{thread_id}_users'
    __cache_key_of_users__ = 'forums_threads_subscriptions_{user_id}'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), primary_key=True)

    @classmethod
    def new(cls,
            *,
            user_id: int,
            thread_id: int) -> Optional['ForumThreadSubscription']:
        ForumThread.is_valid(thread_id, error=True)
        User.is_valid(user_id, error=True)
        return super()._new(
            user_id=user_id,
            thread_id=thread_id)

    @classmethod
    def user_ids_from_thread(cls, id: int) -> List[int]:
        return cls.get_col_from_many(
            key=cls.__cache_key_users__.format(thread_id=id),
            column=cls.user_id,
            filter=cls.thread_id == id)

    @classmethod
    def clear_cache_keys(cls,
                         user_ids: List[int] = None,
                         thread_id: int = None) -> None:
        """
        Clear the cache keys associated with specific users and/or threads. Clearing a thread
        cache key also clears the cache keys for all of its users

        :param user_ids: The IDs of the users whose cache keys should be cleared
        :param thread_id: The ID of the thread for which the cache key should be cleared
        """
        user_ids = user_ids or []  # Don't put a mutable object as default kwarg!
        active_user_ids = user_ids or []
        if thread_id:
            cache.delete(cls.__cache_key_users__.format(thread_id=thread_id))
            active_user_ids += cls.user_ids_from_thread(thread_id)
        if active_user_ids:
            cache.delete_many(
                *(cls.__cache_key_of_users__.format(user_id=uid) for uid in user_ids),
                *(cls.__cache_key_active__.format(user_id=uid) for uid in active_user_ids))


class ForumThreadNote(db.Model, SinglePKMixin):
    __tablename__ = 'forums_threads_notes'
    __cache_key__ = 'forums_threads_notes_{id}'
    __cache_key_of_thread__ = 'forums_threads_notes_thread_{thread_id}'

    __serialize_detailed__ = (
        'id',
        'note',
        'time', )
    __permission_detailed__ = 'modify_forum_threads'

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(
        db.Integer, db.ForeignKey('forums_threads.id'), nullable=False, index=True)
    note = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @classmethod
    def from_thread(cls, thread_id: int) -> List['ForumThreadNote']:
        return cls.get_many(
            key=cls.__cache_key_of_thread__.format(thread_id=thread_id),
            filter=cls.thread_id == thread_id,
            order=cls.time.desc())  # type: ignore

    @classmethod
    def new(cls,
            thread_id: int,
            note: str) -> 'ForumThreadNote':
        ForumThread.is_valid(thread_id, error=True)
        return super()._new(
            thread_id=thread_id,
            note=note)


class ForumPoll(db.Model, SinglePKMixin):
    __tablename__ = 'forums_polls'
    __cache_key__ = 'forums_polls_{id}'
    __cache_key_featured__ = 'forums_polls_featured'
    __cache_key_of_thread__ = 'forums_polls_threads_{thread_id}'

    __serialize__ = (
        'id',
        'thread',
        'question',
        'closed',
        'featured',
        'choices', )
    __serialize_nested_include__ = (
        'thread_id', )
    __serialize_nested_exclude__ = (
        'thread', )

    id: int = db.Column(db.Integer, primary_key=True)
    thread_id: int = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), unique=True)
    question: str = db.Column(db.Text, nullable=False)
    closed: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    featured: bool = db.Column(db.Boolean, nullable=False, server_default='f')

    @declared_attr
    def __table_args__(cls) -> tuple:
        return db.Index('ix_polls_featured', cls.featured, unique=True,
                        postgresql_where=cls.featured == 't'),

    @classmethod
    def from_thread(cls, thread_id: int) -> Optional['ForumPoll']:
        return cls.from_query(
            key=cls.__cache_key_of_thread__.format(thread_id=thread_id),
            filter=cls.thread_id == thread_id)

    @classmethod
    def get_featured(cls) -> Optional['ForumPoll']:
        return cls.from_query(
            key=cls.__cache_key_featured__,
            filter=cls.featured == 't')

    @classmethod
    def new(cls,
            *,
            thread_id: int,
            question: str) -> 'ForumPoll':
        ForumThread.is_valid(thread_id, error=True)
        return cls._new(
            thread_id=thread_id,
            question=question)

    @classmethod
    def unfeature_existing(cls) -> None:
        poll = ForumPoll.get_featured()
        if poll:
            poll.featured = False
            db.session.commit()
            cache.delete(cls.__cache_key_featured__)

    @cached_property
    def choices(self):
        return ForumPollChoice.from_poll(self.id)

    @cached_property
    def thread(self):
        return ForumThread.from_pk(self.thread_id)

    def can_access(self,
                   permission: str = None,
                   error: bool = False) -> bool:
        access = self.thread is not None
        if not access and error:
            raise _403Exception
        return access


class ForumPollChoice(db.Model, SinglePKMixin):
    __tablename__ = 'forums_polls_choices'
    __cache_key__ = 'forums_polls_choice_{id}'
    __cache_key_of_poll__ = 'forums_polls_choices_poll_{poll_id}'
    __cache_key_answers__ = 'forums_polls_{id}_answers'

    __serialize__ = (
        'id',
        'choice',
        'answers', )

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('forums_polls.id'), nullable=False)
    choice = db.Column(db.Text, nullable=False)

    @classmethod
    def from_poll(cls, poll_id: int) -> List['ForumPollChoice']:
        return cls.get_many(
            key=cls.__cache_key_of_poll__.format(poll_id=poll_id),
            filter=cls.poll_id == poll_id,
            order=cls.id.asc())

    @classmethod
    def new(cls,
            *,
            poll_id: int,
            choice: str) -> 'ForumPollChoice':
        ForumPoll.is_valid(poll_id, error=True)
        cache.delete(cls.__cache_key_of_poll__.format(poll_id=poll_id))
        return cls._new(
            poll_id=poll_id,
            choice=choice)

    @classmethod
    def is_valid_choice(cls,
                        pk: int,
                        poll_id: int,
                        error: bool = False) -> bool:
        poll = ForumPoll.from_pk(poll_id, _404=True)
        choice = ForumPollChoice.from_pk(pk, _404=True)
        if poll.id != choice.poll_id:
            if error:
                raise APIException(f'Poll {poll_id} has no answer choice {pk}.')
            return False  # pragma: no cover
        return True

    @cached_property
    def poll(self) -> ForumPoll:
        return ForumPoll.from_pk(self.poll_id)

    @cached_property
    def answers(self):
        return self.count(
            key=self.__cache_key_answers__.format(id=self.id),
            attribute=ForumPollAnswer.user_id,
            filter=ForumPollAnswer.choice_id == self.id)

    def delete_answers(self):
        db.session.execute(
            ForumPollAnswer.__table__.delete().where(
                ForumPollAnswer.choice_id == self.id))
        cache.delete(self.__cache_key_answers__.format(id=self.id))


class ForumPollAnswer(db.Model, MultiPKMixin):
    __tablename__ = 'forums_polls_answers'

    poll_id = db.Column(db.Integer, db.ForeignKey('forums_polls.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    choice_id = db.Column(db.Integer, db.ForeignKey('forums_polls_choices.id'), nullable=False)

    @classmethod
    def new(cls,
            *,
            poll_id: int,
            user_id: int,
            choice_id: bool) -> 'ForumPollAnswer':
        User.is_valid(user_id, error=True)
        # ForumPollChoice also validates ForumPoll.
        ForumPollChoice.is_valid_choice(choice_id, poll_id=poll_id, error=True)
        if cls.from_attrs(poll_id=poll_id, user_id=user_id):
            raise APIException('You have already voted for this poll.')

        cache.delete(ForumPollChoice.__cache_key_answers__.format(id=choice_id))
        return cls._new(
            poll_id=poll_id,
            user_id=user_id,
            choice_id=choice_id)
