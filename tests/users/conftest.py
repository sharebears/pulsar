import pytest

from conftest import (CODE_1, CODE_2, CODE_3, CODE_4, HASHED_CODE_1, HASHED_CODE_2,
                      HASHED_CODE_3)
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO api_keys (user_id, hash, keyhashsalt, revoked, permissions) VALUES
        (1, 'abcdefghij', '{HASHED_CODE_1}', 'f',
         '{{"sample_permission", "sample_2_permission", "sample_3_permission"}}'),
        (1, 'cdefghijkl', '{HASHED_CODE_3}', 'f', '{{}}'),
        (2, 'bcdefghijk', '{HASHED_CODE_3}', 'f', '{{}}'),
        (2, '1234567890', '{HASHED_CODE_2}', 't', '{{}}')""")
    db.engine.execute(
        f"""INSERT INTO invites (inviter_id, invitee_id, email, code, expired) VALUES
        (1, NULL, 'bright@puls.ar', '{CODE_1}', 'f'),
        (1, 2, 'bright@quas.ar', '{CODE_2}', 't'),
        (2, NULL, 'bright@puls.ar', '{CODE_3}', 'f'),
        (1, NULL, 'bright@quas.ar', '{CODE_4}', 't')
         """)
