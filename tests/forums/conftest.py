import pytest

from conftest import add_permissions
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(app, client):
    db.engine.execute(
        """INSERT INTO forums_categories (id, name, description, position, deleted) VALUES
        (1, 'Site', 'General site discussion', 1, 'f'),
        (2, 'General', 'Discussion about your favorite shit', 3, 'f'),
        (3, 'OldGeneral', NULL, 2, 't'),
        (4, 'Redacted', 'Discussion about secret site content', '3', 'f'),
        (5, 'uWhatMate', 'Empty forum', '5', 'f')""")
    db.engine.execute("ALTER SEQUENCE forums_categories_id_seq RESTART WITH 6")
    db.engine.execute(
        """INSERT INTO forums (id, name, description, category_id, position, deleted) VALUES
        (1, 'Pulsar', 'Stuff about pulsar', 1, 1, 'f'),
        (2, 'Bugs', 'Squishy Squash', 1, 2, 'f'),
        (3, 'Bitsu Fan Club', 'Discuss user_three!', 1, 2, 't'),
        (4, '/_\\', 'grey roses die.. the gardens', 2, 10, 'f'),
        (5, 'Yacht Funding', 'First priority', 4, 1, 'f'),
        (6, 'Delet!', 'deleted', 3, 2, 'f')""")
    db.engine.execute("ALTER SEQUENCE forums_id_seq RESTART WITH 7")
    db.engine.execute(
        """INSERT INTO forums_threads (
            id, topic, forum_id, poster_id, locked, sticky, deleted) VALUES
        (1, 'New Site', 1, 1, 'f', 'f', 'f'),
        (2, 'New Site Borked', 1, 1, 't', 'f', 't'),
        (3, 'Using PHP', 2, 2, 't', 't', 'f'),
        (4, 'Literally this', 2, 1, 'f', 'f', 'f'),
        (5, 'Donations?', 5, 1, 'f', 't', 'f')""")
    db.engine.execute("ALTER SEQUENCE forums_threads_id_seq RESTART WITH 6")
    db.engine.execute(
        """INSERT INTO forums_posts (
            id, thread_id, poster_id, contents, time, sticky, edited_user_id, deleted) VALUES
        (1, 2, 1, '!site New yeah', NOW() - INTERVAL '1 MINUTE', 't', NULL, 'f'),
        (2, 3, 1, 'Why the fuck is Gazelle in PHP?!', NOW(), 't', NULL, 'f'),
        (3, 5, 1, 'How do we increase donations?', NOW(), 't', NULL, 'f'),
        (4, 5, 2, 'Since we need a new yacht!', NOW() - INTERVAL '1 MINUTE', 't', NULL, 't'),
        (5, 4, 2, 'Smelly Gazelles!', NOW() - INTERVAL '1 HOUR', 't', NULL, 't'),
        (6, 2, 2, 'Delete this', NOW(), 't', NULL, 'f'),
        (7, 4, 2, 'Dont delete this!', NOW() - INTERVAL '2 MINUTES', 't', NULL, 'f'),
        (8, 4, 1, 'I dont understand this post', NOW() - INTERVAL '3 MINUTES', 'f', NULL, 'f')""")
    db.engine.execute("ALTER SEQUENCE forums_posts_id_seq RESTART WITH 9")
    db.engine.execute(
        """INSERT INTO forums_posts_edit_history (id, post_id, editor_id, contents, time) VALUES
        (1, 1, 1, 'Why the fcuk is Gazelle in HPH?', NOW() - INTERVAL '1 DAY'),
        (3, 3, 2, 'Old typo', NOW() - INTERVAL '1 DAY'),
        (4, 3, 2, 'New typo', NOW() - INTERVAL '1 HOUR'),
        (2, 2, 1, 'Why the shit is Pizzelle in GPG?', NOW() - INTERVAL '12 HOURS')""")
    db.engine.execute("ALTER SEQUENCE forums_posts_edit_history_id_seq RESTART WITH 5")
    db.engine.execute("""INSERT INTO last_viewed_forum_posts (user_id, thread_id, post_id) VALUES
                      (1, 3, 2), (1, 5, 4), (1, 4, 5)""")
    db.engine.execute("""INSERT INTO forums_forums_subscriptions (user_id, forum_id) VALUES
                      (1, 1), (1, 2), (1, 3), (1, 4), (2, 4)""")
    db.engine.execute("""INSERT INTO forums_threads_subscriptions (user_id, thread_id) VALUES
                      (1, 1), (1, 2), (1, 3), (1, 4), (2, 4)""")
    db.engine.execute(
        """INSERT INTO forums_threads_notes (id, thread_id, user_id, note, time) VALUES
        (1, 1, 1, 'NoteA', NOW() - INTERVAL '1 DAY'),
        (2, 1, 1, 'NoteB', NOW() - INTERVAL '23 HOURS'),
        (3, 3, 2, 'NoteC', NOW() - INTERVAL '1 HOUR')""")
    db.engine.execute("ALTER SEQUENCE forums_threads_notes_id_seq RESTART WITH 4")
    db.engine.execute(
        """INSERT INTO forums_polls (id, thread_id, closed, featured, question) VALUES
        (1, 1, 'f', 'f', 'Question 1'),
        (2, 2, 'f', 'f', 'Question 2'),
        (3, 3, 'f', 't', 'Quesiton 3'),
        (4, 4, 't', 'f', 'Question 4')""")
    db.engine.execute("ALTER SEQUENCE forums_polls_id_seq RESTART WITH 5")
    db.engine.execute(
        """INSERT INTO forums_polls_choices (id, poll_id, choice) VALUES
        (1, 1, 'Choice A'),
        (2, 1, 'Choice B'),
        (3, 1, 'Choice C'),
        (4, 2, 'Choice A'),
        (5, 2, 'Choice B'),
        (6, 3, 'Choice A')""")
    db.engine.execute("ALTER SEQUENCE forums_polls_choices_id_seq RESTART WITH 7")
    db.engine.execute(
        """INSERT INTO forums_polls_answers (poll_id, user_id, choice_id) VALUES
        (1, 1, 1),
        (1, 3, 1),
        (1, 2, 2),
        (2, 1, 4)""")

    add_permissions(
        app,
        'forums_forums_permission_1',
        'forums_forums_permission_2',
        'forums_forums_permission_3',
        'forums_forums_permission_4',
        'forums_forums_permission_5',
        'forums_forums_permission_6',
        'forums_threads_permission_1',
        'forums_threads_permission_2',
        'forums_threads_permission_3',
        'forums_threads_permission_4',
        'forums_threads_permission_5',
        table='forums_permissions'
        )
