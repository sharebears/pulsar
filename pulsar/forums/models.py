import flask
from sqlalchemy import func, and_
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from pulsar import db

app = flask.current_app


class Forum(db.Model):
    __tablename__ = 'forums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forums_categories.id'), nullable=False)
    position = db.Column(db.SmallInteger, nullable=False, server_default='0')

    threads = relationship('ForumThread', order_by='ForumThread.last_updated')


class ForumCategories(db.Model):
    __tablename__ = 'forums_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    position = db.Column(db.SmallInteger, nullable=False, server_default='0')
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')


class ForumThread(db.Model):
    __tablename__ = 'forums_threads'

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    locked = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f')
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @declared_attr
    def __table_args__(cls):
        return (db.Index('idx_forums_threads_topic', func.lower(cls.title), unique=True),)

    @property
    def last_updated(self):
        return db.session.query(ForumPost.time).filter(
            ForumPost.thread_id == self.id
            ).order_by(ForumPost.time.asc()).limit(1).first()

    @property
    def post_count(self):
        return db.session.query(func.count(ForumPost.id)).filter(and_(
            (ForumPost.thread_id == self.id),
            (ForumPost.deleted == 'f'),
            )).first()

    @property
    def posts(self):
        return db.session.query(ForumPost).filter(
            ForumPost.thread_id == self.id
            ).order_by(ForumPost.id.asc()).all()


class ForumPost(db.Model):
    __tablename__ = 'forums_posts'

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('forums_threads.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    contents = db.Column(db.Text, nullable=False)
    editable = db.Column(db.Boolean, nullable=False, server_default='f')
    sticky = db.Column(db.Boolean, nullable=False, server_default='f')
    edited_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    deleted = db.Column(db.Boolean, nullable=False, server_default='f')

    @property
    def edit_history(self):
        return db.session.query(ForumPostEdiHistory).filter(
            ForumPostEdiHistory.post_id == self.id
            ).order_by(ForumPostEdiHistory.time.asc()).all()


class ForumPostEdiHistory(db.Model):
    __tablename__ = 'forums_posts_edit_history'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forums_posts.id'), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contents = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
