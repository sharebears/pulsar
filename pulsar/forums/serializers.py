from pulsar.mixins import Serializer, Attribute


class ForumCategorySerializer(Serializer):
    id = Attribute()
    name = Attribute()
    description = Attribute()
    position = Attribute()
    forums = Attribute(nested=False)
    deleted = Attribute(permission='modify_forums')


class ForumSerializer(Serializer):
    id = Attribute()
    name = Attribute()
    description = Attribute()
    category = Attribute(nested=('id',))
    position = Attribute()
    thread_count = Attribute()
    threads = Attribute(nested=False)
    deleted = Attribute(permission='modify_forums')
    last_updated_thread = Attribute()


class ForumThreadSerializer(Serializer):
    id = Attribute()
    topic = Attribute()
    forum = Attribute(nested=('id', ))
    poster = Attribute(nested=('id', 'username', ))
    locked = Attribute()
    sticky = Attribute()
    created_time = Attribute()
    poll = Attribute(nested=False)
    last_post = Attribute()
    last_viewed_post = Attribute()
    subscribed = Attribute()
    post_count = Attribute()
    posts = Attribute(nested=False)
    thread_notes = Attribute(permission='modify_forum_threads')
    deleted = Attribute(permission='modify_forum_threads_advanced')


class ForumPostSerializer(Serializer):
    id = Attribute()
    thread = Attribute(nested=('id', 'topic', ))
    poster = Attribute()
    contents = Attribute()
    time = Attribute()
    edited_time = Attribute()
    sticky = Attribute()
    editor = Attribute()
    deleted = Attribute(permission='modify_forum_posts_advanced', self_access=False)
    edit_history = Attribute(permission='modify_forum_posts_advanced', self_access=False)


class ForumPostEditHistorySerializer(Serializer):
    id = Attribute(permission='modify_forum_posts_advanced')
    editor = Attribute(permission='modify_forum_posts_advanced')
    contents = Attribute(permission='modify_forum_posts_advanced')
    time = Attribute(permission='modify_forum_posts_advanced')


class ForumThreadNoteSerializer(Serializer):
    id = Attribute(permission='modify_forum_threads')
    note = Attribute(permission='modify_forum_threads')
    time = Attribute(permission='modify_forum_threads')


class ForumPollSerializer(Serializer):
    id = Attribute()
    thread = Attribute(nested=('id', 'topic', ))
    question = Attribute()
    closed = Attribute()
    featured = Attribute()
    choices = Attribute()


class ForumPollChoiceSerializer(Serializer):
    id = Attribute()
    choice = Attribute()
    answers = Attribute()
