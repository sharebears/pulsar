import pytest
from pulsar import db
from conftest import CODE_1, CODE_2, HASHED_CODE_1, HASHED_CODE_2, HASHED_CODE_3


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO api_keys (user_id, id, keyhashsalt, revoked, permissions) VALUES
        (1, 'abcdefghij', '{HASHED_CODE_1}', 'f',
         '{{"sample_permission", "sample_2_permission", "sample_3_permission"}}'),
        (1, 'bcdefghijk', '{HASHED_CODE_3}', 'f', '{{}}'),
        (2, '1234567890', '{HASHED_CODE_2}', 't', '{{}}')
        """)
    db.engine.execute(
        """INSERT INTO users_permissions (user_id, permission) VALUES
        (1, 'sample_permission'),
        (1, 'sample_perm_one'),
        (1, 'sample_perm_two')
        """)
    db.engine.execute(
        f"""INSERT INTO sessions (user_id, id, csrf_token, expired) VALUES
        (1, 'abcdefghij', '{CODE_1}', 'f'),
        (2, '1234567890', '{CODE_2}', 't')
        """)
    yield
    db.engine.execute("DELETE FROM api_keys")
    db.engine.execute("DELETE FROM users_permissions")
    db.engine.execute("DELETE FROM sessions")
