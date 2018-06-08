import pytest

from conftest import HASHED_CODE_1, HASHED_CODE_2, HASHED_CODE_3
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO api_keys (user_id, hash, keyhashsalt, revoked, permissions) VALUES
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
