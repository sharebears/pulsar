import pytest

from conftest import add_permissions
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(app, client):
    db.engine.execute(
        """INSERT INTO forums_categories (id, name, description, position, deleted) VALUES
        (1, 'Site', 'General site discussion', 1, 'f'),
        (2, 'General', 'Discussion about your favorite shit', 3, 'f')""")
    db.engine.execute(
        """INSERT INTO forums (id, name, description, category_id, position, deleted) VALUES
        (1, 'Pulsar', 'Stuff about pulsar', 1, 1, 'f'),
        (2, 'Bugs', 'Squishy Squash', 1, 2, 'f')""")
    db.engine.execute(
        """INSERT INTO forums_threads (
            id, topic, forum_id, poster_id, locked, sticky, deleted) VALUES
        (1, 'New Site', 1, 1, 'f', 'f', 'f'),
        (3, 'Using PHP', 2, 2, 't', 't', 'f'),
        (4, 'Literally this', 2, 1, 'f', 'f', 'f')""")
    db.engine.execute("ALTER SEQUENCE forums_threads_id_seq RESTART WITH 6")
    db.engine.execute(
        """INSERT INTO forums_posts (
            id, thread_id, poster_id, contents, time, sticky, edited_user_id, deleted) VALUES
        (2, 3, 1, 'Why the fuck is Gazelle in PHP?!', NOW(), 't', NULL, 'f'),
        (7, 4, 2, 'Dont delete this!', NOW() - INTERVAL '2 MINUTES', 't', NULL, 'f'),
        (8, 4, 1, 'I dont understand this post', NOW() - INTERVAL '3 MINUTES', 'f', NULL, 'f')""")
    db.engine.execute("""INSERT INTO forums_threads_subscriptions (user_id, thread_id) VALUES
                      (1, 3), (1, 4), (2, 4)""")
    add_permissions(
        app,
        'forums_threads_permission_3',
        'forums_threads_permission_4',
        table='forums_permissions'
        )
