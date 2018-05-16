import pytest

from conftest import add_permissions
from pulsar import db


@pytest.fixture(autouse=True)
def populate_db(app, client):
    add_permissions(app, 'list_user_classes', 'modify_user_classes')
    db.engine.execute("""UPDATE user_classes
                      SET permissions = '{"modify_permissions", "edit_settings"}'
                      WHERE name = 'User'""")
    db.engine.execute("""UPDATE secondary_classes
                      SET permissions = '{"send_invites"}'
                      WHERE name = 'FLS'""")
    db.engine.execute("""INSERT INTO user_classes (name, permissions) VALUES
                      ('user_v2', '{"modify_permissions", "edit_settings"}')""")
    db.engine.execute("""INSERT INTO secondary_classes (name, permissions) VALUES
                      ('user_v2', '{"edit_settings"}')""")
