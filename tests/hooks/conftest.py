import pytest

from conftest import CODE_1, CODE_2, CODE_3, HASHED_CODE_1, HASHED_CODE_2
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO sessions (hash, user_id, csrf_token, expired) VALUES
        ('abcdefghij', 1, '{CODE_1}', 'f'),
        ('bcdefghijk', 2, '{CODE_2}', 'f'),
        ('1234567890', 1, '{CODE_3}', 't')
        """)
    db.engine.execute(
        f"""INSERT INTO api_keys (hash, user_id, keyhashsalt, revoked) VALUES
        ('abcdefghij', 1, '{HASHED_CODE_1}', 'f'),
        ('1234567890', 1, '{HASHED_CODE_2}', 't')
        """)
