#!/usr/bin/env python3

import psycopg2

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

conn = psycopg2.connect('postgresql:///pulsar')
cursor = conn.cursor()

cursor.execute("DELETE FROM forums_posts_edit_history")
cursor.execute("DELETE FROM forums_posts")
cursor.execute("DELETE FROM forums_threads")
cursor.execute("DELETE FROM forums")
cursor.execute("DELETE FROM forums_categories")

cursor.execute("DELETE FROM users_permissions")
cursor.execute("DELETE FROM invites")
cursor.execute("DELETE FROM api_keys")
cursor.execute("DELETE FROM sessions")
cursor.execute("DELETE FROM users")
cursor.execute("DELETE from user_classes")
cursor.execute("DELETE FROM secondary_classes")


####################################
####### NEW TABLE INSERTION ### noqa
####################################

# Users System ##########################

cursor.execute("""INSERT INTO user_classes (name, permissions) VALUES
               ('User', '{"view_users", "list_permissions",
                "view_invites", "view_cache_keys", "send_invites"}'),
               ('user_v2', '{"modify_permissions", "list_permissions"}')""")
cursor.execute("""INSERT INTO secondary_classes (name, permissions) VALUES
               ('FLS', '{"send_invites"}'),
               ('user_v2', '{"list_permissions"}')""")
cursor.execute(
    f"""INSERT INTO users (id, username, passhash, email, invites, inviter_id) VALUES
    (1, 'lights', '{HASHED_PASSWORD_1}', 'lights@puls.ar', 1, NULL),
    (2, 'paffu', '{HASHED_PASSWORD_2}', 'paffu@puls.ar', 0, 1)
    """)
cursor.execute("ALTER SEQUENCE users_id_seq RESTART WITH 3")
cursor.execute(
    f"""INSERT INTO invites (inviter_id, email, code, time_sent, active, invitee_id) VALUES
    (1, 'bright@puls.ar', '{CODE_1}', NOW(), 't', NULL),
    (1, 'bitsu@puls.ar', '{CODE_2}', NOW(), 'f', 2),
    (1, 'bright@quas.ar', '{CODE_3}', '2018-03-25 01:09:35.260808+00', 't', NULL)
    """)
cursor.execute(
    f"""INSERT INTO api_keys (user_id, hash, keyhashsalt, active, permissions) VALUES
    (1, 'abcdefghij', '{HASHED_CODE_1}', 't',
        '{{"sample_permission", "sample_2_permission", "sample_3_permission"}}'),
    (1, '0987654321', '{HASHED_CODE_3}','t', '{{}}'),
    (2, '1234567890', '{HASHED_CODE_2}', 'f', '{{}}')
    """)
cursor.execute(
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
cursor.execute(
    f"""INSERT INTO sessions (hash, user_id, csrf_token) VALUES
    ('abcdefghij', 1, '{CODE_1}'),
    ('fc087ea0e6', 1, '8557e86c3d16dc54be6f5468')
    """)

# Forums System ##########################

cursor.execute(
    """INSERT INTO forums_categories (id, name, description, position, deleted) VALUES
    (1, 'Site', 'General site discussion', 1, 'f'),
    (2, 'General', 'Discussion about your favorite shit', 3, 'f'),
    (3, 'OldGeneral', NULL, 2, 't'),
    (4, 'Redacted', 'Discussion about secret site content', '3', 'f')""")
cursor.execute(
    """INSERT INTO forums (id, name, category_id, position, deleted) VALUES
    (1, 'Pulsar', 1, 1, 'f'),
    (2, 'Bugs', 1, 2, 'f'),
    (3, 'Bitsu Fan Club', 1, 2, 't'),
    (4, '/_\\', 2, 10, 'f'),
    (5, 'Yacht Funding', 4, 1, 'f')""")
cursor.execute(
    """INSERT INTO forums_threads (
        id, topic, forum_id, poster_id, locked, sticky, deleted) VALUES
    (1, 'New Site', 1, 1, 'f', 'f', 'f'),
    (2, 'New Site Borked', 1, 1, 't', 'f', 't'),
    (3, 'Using PHP', 2, 2, 't', 't', 'f'),
    (4, 'Literally this', 2, 1, 'f', 'f', 'f'),
    (5, 'Donations?', 5, 1, 'f', 't', 'f')""")
cursor.execute(
    """INSERT INTO forums_posts (
        id, thread_id, poster_id, contents, time, sticky, edited_user_id, deleted) VALUES
    (1, 1, 1, 'Yeah new site bitches!', NOW(), 't', NULL, 'f'),
    (2, 1, 2, 'Right! New Site!!', NOW(), 't', NULL, 'f'),
    (3, 2, 1, '!site New yeah', NOW(), 't', NULL, 'f'),
    (4, 3, 1, 'Why the fuck is Gazelle in PHP?!', NOW(), 't', NULL, 'f'),
    (5, 5, 1, 'How do we increase donations?', NOW(), 't', NULL, 'f'),
    (6, 5, 2, 'Since we need a new yacht!', NOW(), 't', NULL, 't')""")
cursor.execute(
    """INSERT INTO forums_posts_edit_history (id, post_id, editor_id, contents, time) VALUES
    (1, 1, 1, 'Why the fcuk is Gazelle in HPH?', NOW() - 1 DAY),
    (3, 3, 2, 'Old typo', NOW() - 1 DAY),
    (2, 2, 1, 'Why the shit is Pizzelle in GPG?', NOW - 12 HOURS)""")

conn.commit()
conn.close()
