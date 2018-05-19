#!/usr/bin/env python3

import os
import sys

from sqlalchemy.exc import ProgrammingError

from pulsar import create_app, db  # noqa
from pulsar.models import User  # noqa

# Add root project dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


####################################
############ CONSTANTS ######## noqa
####################################

HASHED_PASSWORD_1 = ('pbkdf2:sha256:50000$XwKgylbI$a4868823e7889553e3cb9f'
                     'd922ad08f39c514c2f018cee3c07cd6b9322cc107d')  # 12345
HASHED_PASSWORD_2 = ('pbkdf2:sha256:50000$xH3qCWmd$a82cb27879cce1cb4de401'
                     'fb8c171a42ca19bb0ca7b7e0ba7c6856087e25d3a8')  # abcdefg
HASHED_PASSWORD_3 = ('pbkdf2:sha256:50000$WnhbJYei$7af6aca3be169fb6a8b58b4'
                     'fb666f0325bba59633eb4b4e292afeafbb9f89fa1')

CODE_1 = '1234567890abcdefghij1234'
CODE_2 = 'abcdefghijklmnopqrstuvwx'
CODE_3 = '234567890abcdefghij12345'

HASHED_CODE_1 = ('pbkdf2:sha256:50000$rAUuaX7W$01db64c80f4057c8fdcaddb13cb0'
                 '01c712d7052717df3e38d647aae5eb1ab4f8')
HASHED_CODE_2 = ('pbkdf2:sha256:50000$CH2S6Ojr$71fdc1e523d2e6d063780392c83a'
                 '6b6accbe0ea22bfe44c271e730001181f737')
HASHED_CODE_3 = ('pbkdf2:sha256:50000$DgIO3cu1$cdc9e2d1060c5f339e1cc7cf247d'
                 'f32f49a8f94b4de45b2e149f4c00068ece00')


####################################
######## OLD TABLE DELETION ### noqa
####################################

app = create_app('config.py')
app.app_context().push()

try:
    if User.from_id(10):
        sys.exit("""Database has 10+ users, please wipe it manually if you wish
                 to insert testing data. Example commands:
                 DROP SCHEMA <schemaname> CASCADE;
                 CREATE SCHEMA <schemaname>;
                 GRANT ALL ON SCHEMA <schemaname> TO <user>;
                 GRANT ALL ON SCHEMA <schemaname> to postgres;
                 """)
except ProgrammingError:
    db.session.rollback()
    db.session.close()
    db.session.begin()

db.session.commit()
db.drop_all()
db.create_all()

####################################
####### NEW TABLE INSERTION ### noqa
####################################

# Users System ##########################

db.session.execute(
    """INSERT INTO user_classes (name, permissions) VALUES
    ('User', '{"view_users", "list_permissions",
    "view_invites", "view_cache_keys", "send_invites"}'),
    ('user_v2', '{"modify_permissions", "list_permissions"}')""")
db.session.execute(
    """INSERT INTO secondary_classes (name, permissions) VALUES
    ('FLS', '{"send_invites"}'),
    ('user_v2', '{"list_permissions"}')""")
db.session.execute(
    f"""INSERT INTO users (username, passhash, email, invites, inviter_id) VALUES
    ('lights', '{HASHED_PASSWORD_1}', 'lights@puls.ar', 1, NULL),
    ('paffu', '{HASHED_PASSWORD_2}', 'paffu@puls.ar', 0, 1)
    """)
db.session.execute(
    f"""INSERT INTO invites (inviter_id, email, id, time_sent, expired, invitee_id) VALUES
    (1, 'bright@puls.ar', '{CODE_1}', NOW(), 'f', NULL),
    (1, 'bitsu@puls.ar', '{CODE_2}', NOW(), 't', 2),
    (1, 'bright@quas.ar', '{CODE_3}', '2018-03-25 01:09:35.260808+00', 'f', NULL)
    """)
db.session.execute(
    f"""INSERT INTO api_keys (user_id, id, keyhashsalt, revoked, permissions) VALUES
    (1, 'abcdefghij', '{HASHED_CODE_1}', 'f',
        '{{"sample_permission", "sample_2_permission", "sample_3_permission"}}'),
    (1, '0987654321', '{HASHED_CODE_3}','f', '{{}}'),
    (2, '1234567890', '{HASHED_CODE_2}', 't', '{{}}')
    """)
db.session.execute(
    """INSERT INTO users_permissions (user_id, permission) VALUES
    (1, 'view_api_keys'),
    (1, 'revoke_api_keys'),
    (1, 'modify_permissions'),
    (1, 'list_permissions'),
    (1, 'change_password'),
    (1, 'sample_perm_one'),
    (1, 'sample_perm_two'),
    (1, 'sample_perm_three'),
    (1, 'sample_permission')
    """)
db.session.execute(
    f"""INSERT INTO sessions (id, user_id, csrf_token) VALUES
    ('abcdefghij', 1, '{CODE_1}'),
    ('fc087ea0e6', 1, '8557e86c3d16dc54be6f5468')
    """)

# Forums System ##########################

db.session.execute(
    """INSERT INTO forums_categories (id, name, description, position, deleted) VALUES
    (1, 'Site', 'General site discussion', 1, 'f'),
    (2, 'General', 'Discussion about your favorite shit', 3, 'f'),
    (3, 'OldGeneral', NULL, 2, 't'),
    (4, 'Redacted', 'Discussion about secret site content', '3', 'f'),
    (5, 'uWhatMate', 'Empty forum', '5', 'f')""")
db.session.execute("ALTER SEQUENCE forums_categories_id_seq RESTART WITH 6")
db.session.execute(
    """INSERT INTO forums (id, name, description, category_id, position, deleted) VALUES
    (1, 'Pulsar', 'Stuff about pulsar', 1, 1, 'f'),
    (2, 'Bugs', 'Squishy Squash', 1, 2, 'f'),
    (3, 'Bitsu Fan Club', 'Discuss bitsu!', 1, 2, 't'),
    (4, '/_\\', 'grey roses die.. the gardens', 2, 10, 'f'),
    (5, 'Yacht Funding', 'First priority', 4, 1, 'f')""")
db.session.execute("ALTER SEQUENCE forums_id_seq RESTART WITH 6")
db.session.execute(
    """INSERT INTO forums_threads (
        id, topic, forum_id, poster_id, locked, sticky, deleted) VALUES
    (1, 'New Site', 1, 1, 'f', 'f', 'f'),
    (2, 'New Site Borked', 1, 1, 't', 'f', 't'),
    (3, 'Using PHP', 2, 2, 't', 't', 'f'),
    (4, 'Literally this', 2, 1, 'f', 'f', 'f'),
    (5, 'Donations?', 5, 1, 'f', 't', 'f')""")
db.session.execute("ALTER SEQUENCE forums_threads_id_seq RESTART WITH 6")
db.session.execute(
    """INSERT INTO forums_posts (
        id, thread_id, poster_id, contents, time, sticky, edited_user_id, deleted) VALUES
    (1, 2, 1, '!site New yeah', NOW() - INTERVAL '1 MINUTE', 't', NULL, 'f'),
    (2, 3, 1, 'Why the fuck is Gazelle in PHP?!', NOW(), 't', NULL, 'f'),
    (3, 5, 1, 'How do we increase donations?', NOW(), 't', NULL, 'f'),
    (4, 5, 2, 'Since we need a new yacht!', NOW(), 't', NULL, 't'),
    (5, 4, 2, 'Smelly Gazelles!', NOW() - INTERVAL '1 HOUR', 't', NULL, 't'),
    (6, 2, 2, 'Delete this', NOW(), 't', NULL, 'f')""")
db.session.execute("ALTER SEQUENCE forums_posts_id_seq RESTART WITH 7")
db.session.execute(
    """INSERT INTO forums_posts_edit_history (id, post_id, editor_id, contents, time) VALUES
    (1, 1, 1, 'Why the fcuk is Gazelle in HPH?', NOW() - INTERVAL '1 DAY'),
    (3, 3, 2, 'Old typo', NOW() - INTERVAL '1 DAY'),
    (4, 3, 2, 'New typo', NOW() - INTERVAL '1 HOUR'),
    (2, 2, 1, 'Why the shit is Pizzelle in GPG?', NOW() - INTERVAL '12 HOURS')""")
db.session.execute("ALTER SEQUENCE forums_posts_edit_history_id_seq RESTART WITH 5")

db.session.commit()
