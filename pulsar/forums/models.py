from datetime import datetime
from typing import List, Optional

import flask
from sqlalchemy import and_, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select
from sqlalchemy.sql.elements import BinaryExpression

from pulsar import cache, db
from pulsar.mixin import ModelMixin
from pulsar.models import User

app = flask.current_app


class ForumCategory(db.Model, ModelMixin):
    __tablename__ = 'forums_categories'
    __cache_key__ = 'forums_categories_{id}'
    __cache_key_all__ = 'forums_categories_all'

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
    description: str = db.Column(db.Text)
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

    @property
    def forums(self) -> List['Forum']:
        return Forum.from_category(self.id)


class Forum(db.Model, ModelMixin):
    __tablename__ = 'forums'
    __cache_key__ = 'forums_{id}'
    __cache_key_last_updated__ = 'forums_{id}_last_updated'
    __cache_key_thread_count__ = 'forums_{id}_thread_count'
    __cache_key_of_category__ = 'forums_forums_of_categories_{id}'

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
    description: str = db.Column(db.Text)
    category_id: int = db.Column(
        db.Integer, db.ForeignKey('forums_categories.id'), nullable=False, index=True)
    position: bool = db.Column(db.SmallInteger, nullable=False, server_default='0')
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

    @property
    def category(self) -> 'ForumCategory':
        return ForumCategory.from_id(self.category_id)

    @property
    def thread_count(self) -> 'int':
        return self.count(
            key=self.__cache_key_thread_count__.format(id=self.id),
            attribute=ForumThread.id,
            filter=and_(ForumThread.forum_id == self.id, ForumThread.deleted == 'f'))

    @property
    def last_updated_thread(self) -> Optional['ForumThread']:
        return ForumThread.from_query(
            key=self.__cache_key_last_updated__.format(id=self.id),
            filter=(ForumThread.forum_id == self.id),
            order=ForumThread.last_updated.desc())

    @property
    def threads(self) -> List['ForumThread']:
        if hasattr(self, '_threads'):
            return self._threads
        return ForumThread.from_forum(self.id, 1, limit=50)

    def set_threads(self,
                    page: int,
                    limit: int,
                    include_dead: bool = False) -> None:
        self._threads = ForumThread.from_forum(self.id, page, limit, include_dead)


class ForumThread(db.Model, ModelMixin):
    __tablename__ = 'forums_threads'
    __cache_key__ = 'forums_threads_{id}'
    __cache_key_post_count__ = 'forums_threads_{id}_post_count'
    __cache_key_of_forum__ = 'forums_threads_forums_{id}'
    __cache_key_last_post__ = 'forums_threads_{id}_last_post'

    __serialize__ = (
        'id',
        'topic',
        'forum',
        'poster',
        'locked',
        'sticky',
        'created_time',
        'last_post',
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
        return db.Index('ix_forums_threads_topic', func.lower(cls.topic), unique=True),

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
            limit=limit)

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

    @property
    def last_post(self) -> Optional['ForumPost']:
        return ForumPost.from_query(
            key=self.__cache_key_last_post__.format(id=self.id),
            filter=and_(
                ForumPost.thread_id == self.id,
                ForumPost.deleted == 'f'),
            order=ForumPost.id.desc())

    @hybrid_property
    def last_updated(cls) -> BinaryExpression:
        return select([func.max(ForumPost.time)]).where(ForumPost.thread_id == cls.id).as_scalar()

    @property
    def forum(self) -> 'Forum':
        return Forum.from_id(self.forum_id)

    @property
    def poster(self) -> User:
        return User.from_id(self.poster_id)

    @property
    def post_count(self) -> int:
        return self.count(
            key=self.__cache_key_post_count__.format(id=self.id),
            attribute=ForumPost.id,
            filter=and_(ForumPost.thread_id == self.id, ForumPost.deleted == 'f',))

    @property
    def posts(self) -> List['ForumPost']:
        if hasattr(self, '_posts'):
            return self._posts
        return ForumPost.from_thread(self.id, 1, limit=50)

    def set_posts(self,
                  page: int = 1,
                  limit: int = 50,
                  include_dead: bool = False) -> None:
        self._posts = ForumPost.from_thread(self.id, page, limit, include_dead)


class ForumPost(db.Model, ModelMixin):
    __tablename__ = 'forums_posts'
    __cache_key__ = 'forums_posts_{id}'
    __cache_key_of_thread__ = 'forums_posts_threads_{id}'

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

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    contents = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    sticky = db.Column(db.Boolean, nullable=False, server_default='f')
    edited_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    edited_time = db.Column(db.DateTime(timezone=True))
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @classmethod
    def from_thread(cls,
                    thread_id: int,
                    page: int = 1,
                    limit: int = 50,
                    include_dead: bool = False) -> List['ForumPost']:
        return cls.get_many(
            key=cls.__cache_key_of_thread__.format(id=thread_id),
            filter=cls.thread_id == thread_id,
            order=cls.id.asc(),
            page=page,
            limit=limit)

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

    @property
    def poster(self) -> User:
        return User.from_id(self.poster_id)

    @property
    def editor(self) -> Optional[User]:
        return User.from_id(self.edited_user_id)

    @property
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

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forums_posts.id'), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contents = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @classmethod
    def from_post(cls, post_id: int) -> List['ForumPostEditHistory']:
        return cls.get_many(
            key=cls.__cache_key_of_post__.format(id=post_id),
            filter=cls.post_id == post_id,
            order=cls.id.desc())

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

    @property
    def editor(self) -> User:
        return User.from_id(self.editor_id)
