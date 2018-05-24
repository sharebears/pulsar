from datetime import datetime
from typing import List, Optional

import flask
from sqlalchemy import and_, func, select
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import BinaryExpression

from pulsar import _403Exception, cache, db
from pulsar.mixins import ModelMixin
from pulsar.users.models import User
from pulsar.permissions.models import ForumPermission
from pulsar.utils import cached_property

app = flask.current_app


class ForumCategory(db.Model, ModelMixin):
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
    position: int = db.Column(db.SmallInteger, nullable=False, server_default='0')
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f')

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


class Forum(db.Model, ModelMixin):
    __tablename__ = 'forums'
    __cache_key__ = 'forums_{id}'
    __cache_key_last_updated__ = 'forums_{id}_last_updated'
    __cache_key_thread_count__ = 'forums_{id}_thread_count'
    __cache_key_of_category__ = 'forums_forums_of_categories_{id}'
    __cache_key_of_subscribed__ = 'forums_forums_subscriptions_{user_id}'
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
    position: int = db.Column(db.SmallInteger, nullable=False, server_default='0')
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f')

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
            key=ForumSubscription.__cache_key__.format(user_id=user_id),
            filter=cls.id.in_(db.session.query(ForumSubscription.forum_id)  # type: ignore
                              .filter(ForumSubscription.user_id == user_id)),
            order=Forum.id.asc())  # type: ignore

    @cached_property
    def category(self) -> 'ForumCategory':
        return ForumCategory.from_id(self.category_id)

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
        access = (flask.g.user is not None and (
            flask.g.user.has_permission(self.__permission_key__.format(id=self.id))
            or (permission is not None and flask.g.user.has_permission(permission))))
        if error and not access:
            raise _403Exception
        return access


class ForumThread(db.Model, ModelMixin):
    __tablename__ = 'forums_threads'
    __cache_key__ = 'forums_threads_{id}'
    __cache_key_post_count__ = 'forums_threads_{id}_post_count'
    __cache_key_of_forum__ = 'forums_threads_forums_{id}'
    __cache_key_of_subscribed__ = 'forums_threads_subscriptions_{user_id}'
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
        'last_post',
        'last_viewed_post',
        'post_count',
        'posts')
    __serialize_very_detailed__ = (
        'deleted', )
    __serialize_nested_exclude__ = (
        'forum',
        'posts')

    __permission_very_detailed__ = 'modify_forum_threads_advanced'

    _posts: List['ForumPost']

    id: int = db.Column(db.Integer, primary_key=True)
    topic: str = db.Column(db.String(150), nullable=False)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False)  # type: int
    poster_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_time: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    locked: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f')

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
        return cls.get_ids_of_many(
            key=cls.__cache_key_of_forum__.format(id=id),
            filter=cls.forum_id == id,
            order=cls.last_updated.desc())

    @classmethod
    def from_subscribed_user(cls, user_id: int) -> List['ForumThread']:
        return cls.get_many(
            key=ForumThreadSubscription.__cache_key__.format(user_id=user_id),
            filter=cls.id.in_(db.session.query(ForumThreadSubscription.thread_id)  # type: ignore
                              .filter(ForumThreadSubscription.user_id == user_id)),
            order=ForumThread.id.asc())  # type: ignore

    @hybrid_property
    def last_updated(cls) -> BinaryExpression:
        return select([func.max(ForumPost.time)]).where(ForumPost.thread_id == cls.id).as_scalar()

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
        return Forum.from_id(self.forum_id)

    @cached_property
    def poster(self) -> User:
        return User.from_id(self.poster_id)

    @cached_property
    def post_count(self) -> int:
        return self.count(
            key=self.__cache_key_post_count__.format(id=self.id),
            attribute=ForumPost.id,
            filter=and_(ForumPost.thread_id == self.id, ForumPost.deleted == 'f',))

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


class ForumPost(db.Model, ModelMixin):
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
    thread_id: int = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), nullable=False)
    poster_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    contents: str = db.Column(db.Text, nullable=False)
    time: datetime = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now())
    sticky: bool = db.Column(db.Boolean, nullable=False, server_default='f')
    edited_user_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('users.id'))
    edited_time: Optional[datetime] = db.Column(db.DateTime(timezone=True))
    deleted: bool = db.Column(db.Boolean, nullable=False, server_default='f')

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
        return cls.get_ids_of_many(
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
        return User.from_id(self.poster_id)

    @cached_property
    def editor(self) -> Optional[User]:
        return User.from_id(self.edited_user_id)

    @cached_property
    def edit_history(self) -> List['ForumPostEditHistory']:
        return ForumPostEditHistory.from_post(self.id)


class ForumPostEditHistory(db.Model, ModelMixin):
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
        return User.from_id(self.editor_id)


# Denormalized thread id and post id for efficiency's sake
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
        post = ForumPost.from_id(post_id, include_dead=True)
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


class ForumSubscription(db.Model):
    __tablename__ = 'forums_forums_subscriptions'
    __cache_key__ = 'forums_forums_subscriptions_{user_id}'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id'), primary_key=True)


class ForumThreadSubscription(db.Model):
    __tablename__ = 'forums_threads_subscriptions'
    __cache_key__ = 'forums_threads_subscriptions_{user_id}'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), primary_key=True)
