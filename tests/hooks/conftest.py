import pytest
from conftest import CODE_1, CODE_2, HASHED_CODE_1
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        f"""INSERT INTO sessions (id, user_id, csrf_token) VALUES
        ('abcdefghij', 1, '{CODE_1}'),
        ('bcdefghijk', 2, '{CODE_2}')
        """)
    db.engine.execute(
        f"""INSERT INTO api_keys (id, user_id, keyhashsalt) VALUES
        ('abcdefghij', 1, '{HASHED_CODE_1}')
        """)
    yield
    db.engine.execute("DELETE FROM api_keys")
    db.engine.execute("DELETE FROM sessions")
