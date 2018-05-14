import flask
from sqlalchemy import func, and_
from sqlalchemy.sql import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from pulsar import db

app = flask.current_app


class ForumCategory(db.Model):
    __tablename__ = 'forums_categories'
    __cache_key__ = 'forums_categories_{id}'
    __cache_key_all__ = 'forums_categories_all'

    __serialize__ = ('id', 'name', 'description', 'position', 'forums', )
    __serialize_detailed__ = ('deleted', )
    __serialize_nested_exclude__ = ('forums', )

    __permission_detailed__ = 'modify_forums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    position = db.Column(db.SmallInteger, nullable=False, server_default='0')
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @classmethod
    def get_all(cls, include_dead=False):
        return cls.get_many(
            key=cls.__cache_key_all__,
            order=cls.position.asc(),
            required_properties=('forums', ))

    @classmethod
    def new(cls, name, description, position):
        return super().new(
            name=name,
            description=description,
            position=position)

    @property
    def cache_key(self):
        return self.__cache_key__.format(id=self.id)

    @property
    def forums(self):
        return Forum.from_category(self.id)


class Forum(db.Model):
    __tablename__ = 'forums'
    __cache_key__ = 'forums_{id}'
    __cache_key_last_updated__ = 'forums_{id}_last_updated'
    __cache_key_thread_count__ = 'forums_{id}_thread_count'
    __cache_key_of_category__ = 'forums_forums_categories_{id}'

    __serialize__ = ('id', 'name', 'description', 'category', 'position',
                     'thread_count', 'threads', )
    __serialize_very_detailed__ = ('deleted', )
    __serialize_nested_include = ('last_updated_thread', )
    __serialize_nested_exclude__ = ('category', 'threads', )

    __permission_very_detailed__ = 'modify_forum_threads_advanced'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(
        db.Integer, db.ForeignKey('forums_categories.id'), nullable=False, index=True)
    position = db.Column(db.SmallInteger, nullable=False, server_default='0')
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @classmethod
    def from_category(cls, category_id):
        return cls.get_many(
            key=cls.__cache_key_of_category__.format(id=category_id),
            filter=cls.category_id == category_id,
            order=cls.position.asc())

    @classmethod
    def new(cls, name, description, category_id, position):
        category = ForumCategory.from_id(category_id)
        if not category or category.deleted:
            return None
        return super().new(
            name=name,
            description=description,
            category_id=category_id,
            position=position)

    @property
    def cache_key(self):
        return self.__cache_key__.format(id=self.id)

    @property
    def category(self):
        return ForumCategory.from_id(self.category_id)

    @property
    def thread_count(self):
        return self.count(
            key=self.__cache_key_thread_count__.format(id=self.id),
            attribute=ForumThread.id,
            filter=and_(ForumThread.forum_id == self.id, ForumThread.deleted == 'f'))

    @property
    def last_updated_thread(self):
        return ForumThread.from_query(
            key=self.__cache_key_last_updated__.format(id=self.id),
            filter=(ForumThread.forum_id == self.id),
            order=ForumThread.last_updated.desc())

    @property
    def threads(self):
        if hasattr(self, '_threads'):
            return self._threads
        return ForumThread.from_forum(self.id, 1, limit=50)

    def set_threads(self, page, limit, include_dead=False):
        self._threads = ForumThread.from_forum(self.id, page, limit, include_dead)


class ForumThread(db.Model):
    __tablename__ = 'forums_threads'
    __cache_key__ = 'forums_threads_{id}'
    __cache_key_post_count__ = 'forums_threads_{id}_post_count'
    __cache_key_posts__ = 'forums_threads_{id}_posts'
    __cache_key_of_forum__ = 'forums_threads_forums_{id}'
    __cache_key_last_post__ = 'forums_threads_{id}_last_post'

    __serialize__ = ('id', 'topic', 'forum', 'poster', 'locked',
                     'sticky', 'last_updated', 'post_count', 'posts')
    __serialize_very_detailed__ = ('deleted', )
    __serialize_nested_exclude__ = ('forum', 'posts')

    __permission_very_detailed__ = 'modify_forum_threads_advanced'

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    locked = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f')
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_forums_threads_topic', func.lower(cls.topic), unique=True),)

    @classmethod
    def from_forum(cls, forum_id, page=1, limit=50, include_dead=False):
        return cls.get_many(
            key=cls.__cache_key_of_forum__.format(id=forum_id),
            filter=(cls.forum_id == forum_id),
            order=cls.last_updated.desc(),
            page=page,
            limit=limit)

    @classmethod
    def new(cls, topic, forum_id, poster_id):
        from pulsar.models import User
        forum = Forum.from_id(forum_id)
        if not forum or forum.deleted or not User.from_id(poster_id):
            return None
        return super().new(
            topic=topic,
            forum_id=forum_id,
            poster_id=poster_id)

    @property
    def last_post(self):
        return ForumPost.from_query(
            key=self.__cache_key_last_post__.format(id=self.id),
            filter=(ForumPost.thread_id == self.id),
            order=ForumPost.id.desc())

    @hybrid_property
    def last_updated(cls):
        return select([func.max(ForumPost.time)]).where(ForumPost.thread_id == cls.id).as_scalar()

    @property
    def forum(self):
        return Forum.from_id(self.forum_id)

    @property
    def poster(self):
        from pulsar.models import User
        return User.from_id(self.poster_id)

    @property
    def post_count(self):
        return self.count(
            key=self.__cache_key_post_count__.format(id=self.id),
            attribute=ForumPost.id,
            filter=and_(ForumPost.thread_id == self.id, ForumPost.deleted == 'f',))

    @property
    def posts(self):
        if hasattr(self, '_posts'):
            return self._posts
        return ForumPost.from_thread(self.id, 1, limit=50)

    def set_posts(self, page=1, limit=50, include_dead=False):
        self._posts = ForumPost.from_thread(self.id, page, limit, include_dead)


class ForumPost(db.Model):
    __tablename__ = 'forums_posts'
    __cache_key__ = 'forums_posts_{id}'
    __cache_key_of_thread__ = 'forums_posts_threads_{id}'

    __serialize__ = ('id', 'thread_id', 'poster', 'contents', 'time', 'sticky', 'editor', )
    __serialize_very_detailed__ = ('deleted', 'edit_history', )
    __serialize_nested_exclude__ = ('thread_id', )

    __permission_very_detailed__ = 'modify_forum_posts_advanced'

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    contents = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    sticky = db.Column(db.Boolean, nullable=False, server_default='f')
    edited_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @classmethod
    def from_thread(cls, thread_id, page=1, limit=50, include_dead=False):
        return cls.get_many(
            key=cls.__cache_key_of_thread__.format(id=thread_id),
            filter=cls.thread_id == thread_id,
            order=cls.id.asc(),
            page=page,
            limit=limit)

    @classmethod
    def new(cls, thread_id, poster_id, contents):
        from pulsar.models import User
        thread = ForumThread.from_id(thread_id)
        poster = User.from_id(poster_id)
        if not thread or thread.deleted or not poster:
            return None
        return super().new(
            thread_id=thread_id,
            poster_id=poster_id,
            contents=contents)

    @property
    def poster(self):
        from pulsar.models import User
        return User.from_id(self.poster_id)

    @property
    def editor(self):
        from pulsar.models import User
        return User.from_id(self.edited_user_id)

    @property
    def edit_history(self):
        return ForumPostEditHistory.from_post(self.id)


class ForumPostEditHistory(db.Model):
    __tablename__ = 'forums_posts_edit_history'
    __cache_key__ = 'forums_posts_edit_history_{id}'
    __cache_key_of_post__ = 'forums_posts_edit_history_posts_{id}'

    __serialize_detailed__ = ('id', 'post', 'editor', 'contents', 'time', )
    __serialize_nested_exclude__ = ('post', )

    __permission_detailed__ = 'modify_forum_posts_advanced'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forums_posts.id'), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contents = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @classmethod
    def from_post(cls, post_id):
        return cls.get_many(
            key=cls.__cache_key_of_post__.format(id=post_id),
            filter=cls.post_id == post_id,
            order=cls.id.desc())

    @property
    def post(self):
        return ForumPost.from_id(self.post_id)

    @property
    def editor(self):
        from pulsar.models import User
        return User.from_id(self.editor_id)
