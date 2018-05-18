import pytest

from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(client):
    db.engine.execute(
        """INSERT INTO users_permissions (user_id, permission) VALUES
        (1, 'sample_perm_one'),
        (1, 'sample_perm_two'),
        (1, 'sample_perm_three')
        """)
