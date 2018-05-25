import pytest

from conftest import CODE_1, CODE_2, CODE_3, CODE_4
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(app, client):
    db.engine.execute(
        f"""INSERT INTO invites (inviter_id, invitee_id, email, code, expired) VALUES
        (1, NULL, 'bright@puls.ar', '{CODE_1}', 'f'),
        (1, 2, 'bright@quas.ar', '{CODE_2}', 't'),
        (2, NULL, 'bright@puls.ar', '{CODE_3}', 'f'),
        (1, NULL, 'bright@quas.ar', '{CODE_4}', 't')
         """)
