import flask
from sqlalchemy import func, and_
from sqlalchemy.sql import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from pulsar import db, cache

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
    def from_id(cls, id, include_dead=False):
        forum_category = cls.from_cache(
            key=cls.__cache_key__.format(id=id),
            query=cls.query.filter(cls.id == id))
        if forum_category and (include_dead or not forum_category.deleted):
            return forum_category
        return None

    @classmethod
    def get_all(cls, include_dead=False):
        cache_key = cls.__cache_key_all__
        category_ids = cache.get(cache_key)
        if not category_ids:
            category_ids = [
                c[0] for c in
                db.session.query(cls.id).order_by(cls.position.asc()).all()]
            cache.set(cache_key, category_ids)

        categories = []
        for category_id in category_ids:
            categories.append(cls.from_id(category_id, include_dead=include_dead))
        return categories

    @classmethod
    def new(cls, name, description, position):
        category = cls(name=name, description=description, position=position)
        db.session.add(category)
        db.session.commit()
        cache.cache_model(category.cache_key, category)
        return category

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
    __cache_key_of_category__ = 'forums_categories_{id}'

    __serialize__ = ('id', 'name', 'category', 'position', 'thread_count', 'last_updated_thread', )
    __serialize_very_detailed__ = ('deleted', )
    __serialize_nested_exclude__ = ('category', )

    __permission_very_detailed__ = 'modify_forum_threads_advanced'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey('forums_categories.id'), nullable=False, index=True)
    position = db.Column(db.SmallInteger, nullable=False, server_default='0')
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @classmethod
    def from_id(cls, id, include_dead=False):
        forum = cls.from_cache(
            key=cls.__cache_key__.format(id=id),
            query=cls.query.filter(cls.id == id))
        if forum and (include_dead or not forum.deleted):
            return forum
        return None

    @classmethod
    def from_category(cls, category_id):
        cache_key = cls.__cache_key_of_category__.format(id=category_id)
        forum_ids = cache.get(cache_key)
        if not forum_ids:
            forum_ids = [f[0] for f in db.session.query(cls.id).filter(
                cls.category_id == category_id
                ).order_by(cls.position.asc()).all()]
            cache.set(cache_key, forum_ids)

        forums = []
        for forum_id in forum_ids:
            forum = cls.from_id(id)
            if forum:
                forums.append(forum)
        return forums

    @property
    def cache_key(self):
        return self.__cache_key__.format(id=self.id)

    @property
    def category(self):
        return ForumCategory.from_id(self.category_id)

    @property
    def thread_count(self):
        cache_key = self.__cache_key_thread_count__.format(id=self.id)
        thread_count = cache.get(cache_key)
        if not thread_count:
            thread_count = db.session.query(func.count(ForumThread.id)).filter(
                ForumThread.forum_id == self.id).first()
            cache.set(cache_key, thread_count)
        return thread_count

    @property
    def last_updated_thread(self):
        cache_key = self.__cache_key_last_updated__.format(id=self.id)
        thread_id = cache.get(cache_key)
        if not thread_id:
            thread = ForumThread.query.filter(
                ForumThread.forum_id == self.id
                ).order_by(ForumThread.last_updated).limit(1).first()
            cache.set(cache_key, thread.id)
            return thread
        return ForumThread.from_id(thread_id)

    @property
    def threads(self):
        if hasattr(self, '_threads'):
            return self._threads
        return ForumThread.from_forum(self.id, 1, 50)

    def thread_setter(self, page, limit, include_dead=False):
        self._threads = ForumThread.from_forum(self.id, page, limit, include_dead)


class ForumThread(db.Model):
    __tablename__ = 'forums_threads'
    __cache_key__ = 'forums_threads_{id}'
    __cache_key_post_count__ = 'forums_threads_{id}_post_count'
    __cache_key_posts__ = 'forums_threads_{id}_posts'
    __cache_key_of_forum__ = 'forums_threads_forums_{id}'
    __cache_key_last_updated = 'forums_threads_{id}_last_updated'

    __serialize__ = ('id', 'topic', 'forum', 'poster', 'locked',
                     'sticky', 'last_updated', 'post_count', )
    __serialize_very_detailed__ = ('deleted', )
    __serialize_nested_exclude__ = ('forum', )

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
        return (db.Index('idx_forums_threads_topic', func.lower(cls.topic), unique=True),)

    @classmethod
    def from_id(cls, id, include_dead=False):
        forum_thread = cls.from_cache(
            key=cls.__cache_key__.format(id=id),
            query=cls.query.filter(cls.id == id))
        if forum_thread and (include_dead or not forum_thread.deleted):
            return forum_thread
        return None

    @classmethod
    def from_forum(cls, forum_id, page, limit=50, include_dead=False):
        cache_key = cls.__cache_key_of_forum__.format(id=forum_id)
        thread_ids = cache.get(cache_key)
        if not thread_ids:
            thread_ids = [t[0] for t in db.session.query(cls.thread_id).filter(
                cls.forum_id == forum_id
                ).order_by(cls.last_updated.desc()).all()]
            cache.set(cache_key, thread_ids)

        threads = []
        num_threads = 0
        for thread_id in thread_ids[page * limit + 1:]:
            threads.append(cls.from_id(thread_id))
            num_threads += 1
            if num_threads >= limit:
                break
        return threads

    @hybrid_property
    def last_updated(self):
        cache_key = self.__cache_key_last_updated.format(id=self.id)
        last_updated = cache.get(cache_key)
        if not last_updated:
            last_updated = db.session.query(ForumPost.time).filter(
                ForumPost.thread_id == self.id
                ).order_by(ForumPost.time.desc()).limit(1).first()
            cache.set(cache_key, last_updated)
        return last_updated

    @last_updated.expression
    def last_updated(cls):
        return select(func.max(ForumPost.time)).where(ForumPost.thread_id == cls.id)

    @property
    def forum(self):
        return Forum.from_id(self.forum_id)

    @property
    def poster(self):
        from pulsar.models import User
        return User.from_id(self.poster_id)

    @property
    def post_count(self):
        cache_key = self.__cache_key_post_count__.format(id=self.id)
        post_count = cache.get(cache_key)
        if not post_count:
            post_count = db.session.query(func.count(ForumPost.id)).filter(and_(
                (ForumPost.thread_id == self.id),
                (ForumPost.deleted == 'f'),
                )).first()
            cache.set(cache_key, post_count)
        return post_count

    @property
    def posts(self):
        if hasattr(self, '_posts'):
            return self._posts
        return ForumPost.from_thread(self.id, 1, 50)

    def set_posts(self, page, limit=50, include_dead=False):
        self._posts = ForumPost.from_thread(self.id, page, limit, include_dead)


class ForumPost(db.Model):
    __tablename__ = 'forums_posts'
    __cache_key = 'forums_posts_{id}'
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
    def from_id(cls, id, include_dead=False):
        forum_post = cls.from_cache(
            key=cls.__cache_key__.format(id=id),
            query=cls.query.filter(cls.id == id))
        if forum_post and (include_dead or not forum_post.deleted):
            return forum_post
        return None

    @classmethod
    def from_thread(cls, thread_id, page, limit=50, include_dead=False):
        cache_key = cls.__cache_key_of_thread__.format(id=thread_id)
        post_ids = cache.get(cache_key)
        if not post_ids:
            post_ids = [p[0] for p in db.session.query(cls.id).filter(
                cls.thread_id == thread_id
                ).order_by(cls.id.asc()).all()]
            cache.set(cache_key, post_ids)

        posts = []
        num_posts = 0
        for post_id in post_ids[page * limit + 1:]:
            post = cls.from_id(post_id)
            if include_dead or not post.deleted:
                posts.append(cls.from_id(post_id))
                num_posts += 1
                if num_posts >= limit:
                    break
        return posts

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
    def from_id(cls, id):
        return cls.from_cache(
            key=cls.__cache_key__.format(id=id),
            query=cls.query.filter(cls.id == id))

    @classmethod
    def from_post(cls, post_id):
        return cls.from_cache(
            key=cls.__cache_key_of_post__.format(id=post_id),
            query=cls.query.filter(cls.post_id == post_id).order_by(cls.time.desc()))

    @property
    def post(self):
        return ForumPost.from_id(self.post_id)

    @property
    def editor(self):
        from pulsar.models import User
        return User.from_id(self.editor_id)
