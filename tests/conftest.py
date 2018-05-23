import os
import sys
from collections import defaultdict
from contextlib import contextmanager

import flask
import pytest

from pulsar import cache, create_app, db
from pulsar.users.models import User

HASHED_PASSWORD_1 = ('pbkdf2:sha256:50000$XwKgylbI$a4868823e7889553e3cb9f'
                     'd922ad08f39c514c2f018cee3c07cd6b9322cc107d')  # 12345
HASHED_PASSWORD_2 = ('pbkdf2:sha256:50000$xH3qCWmd$a82cb27879cce1cb4de401'
                     'fb8c171a42ca19bb0ca7b7e0ba7c6856087e25d3a8')  # abcdefg
HASHED_PASSWORD_3 = ('pbkdf2:sha256:50000$WnhbJYei$7af6aca3be169fb6a8b58b4'
                     'fb666f0325bba59633eb4b4e292afeafbb9f89fa1')

CODE_1 = '1234567890abcdefghij1234'
CODE_2 = 'abcdefghijklmnopqrstuvwx'
CODE_3 = '234567890abcdefghij12345'
CODE_4 = 'zbjfeaofe38232r2qpfewfoo'

HASHED_CODE_1 = ('pbkdf2:sha256:50000$rAUuaX7W$01db64c80f4057c8fdcaddb13cb0'
                 '01c712d7052717df3e38d647aae5eb1ab4f8')
HASHED_CODE_2 = ('pbkdf2:sha256:50000$CH2S6Ojr$71fdc1e523d2e6d063780392c83a'
                 '6b6accbe0ea22bfe44c271e730001181f737')
HASHED_CODE_3 = ('pbkdf2:sha256:50000$DgIO3cu1$cdc9e2d1060c5f339e1cc7cf247d'
                 'f32f49a8f94b4de45b2e149f4c00068ece00')


sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_json_response(response, expected, list_=False, strict=False):
    "Helper function to assert the JSON response matches the expected response."
    response_full = response.get_json()
    assert 'response' in response_full
    response = response_full['response']
    check_dictionary(response, expected, list_, strict)


def check_dictionary(response, expected, list_=False, strict=False):
    if strict:
        assert response == expected
    else:
        if list_:
            assert isinstance(response, list) and response
            response = response[0]

        if isinstance(expected, str):
            assert response == expected
        else:
            for key, value in expected.items():
                assert key in response and value == response[key]


def add_permissions(app_, *permissions, table='users_permissions'):
    "Insert permissions into database for user_id 1 (authed user)."
    assert isinstance(app_, flask.Flask)
    db.engine.execute(
        f"""INSERT INTO {table} (user_id, permission) VALUES
        (1, '""" + "'), (1, '".join(permissions) + "')")


def check_dupe_in_list(list_):
    seen = set()
    for v in list_:
        if v in seen:
            return False
        seen.add(v)
    return True


@pytest.fixture(autouse=True, scope='session')
def db_create_tables():
    app = create_app('test_config.py')
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield
    with app.app_context():
        db.drop_all()


@pytest.fixture
def app(monkeypatch):
    app = create_app('test_config.py')
    cache.clear()
    with app.app_context():
        unpopulate_db()
        populate_db()
    yield app


@pytest.fixture
def client(app):
    with set_globals(app):
        with app.app_context():
            yield app.test_client()


@pytest.fixture
def authed_client(app, monkeypatch):
    monkeypatch.setattr(app, 'before_request_funcs', {})
    with set_globals(app):
        with app.app_context():
            user = User.from_id(1)
    with set_globals(app):
        with set_user(app, user):
            with app.app_context():
                db.session.add(user)
                yield app.test_client()


@contextmanager
def set_globals(app_):
    def handler(sender, **kwargs):
        flask.g.cache_keys = defaultdict(set)
        flask.g.api_key = None
        flask.g.user_session = None
        if not hasattr(flask.g, 'user'):
            flask.g.user = None
    with flask.appcontext_pushed.connected_to(handler, app_):
        yield


@contextmanager
def set_user(app_, user):
    def handler(sender, **kwargs):
        flask.g.user = user
    with flask.appcontext_pushed.connected_to(handler, app_):
        yield


def populate_db():
    "Populate the database with test user information."
    db.engine.execute("""INSERT INTO user_classes (name) VALUES ('User')""")
    db.engine.execute("""INSERT INTO secondary_classes (name) VALUES ('FLS')""")
    db.engine.execute(
        f"""INSERT INTO users (username, passhash, email, invites, inviter_id, user_class_id) VALUES
        ('lights', '{HASHED_PASSWORD_1}', 'lights@puls.ar', 1, NULL, 1),
        ('paffu', '{HASHED_PASSWORD_2}', 'paffu@puls.ar', 0, 1, 1),
        ('bitsu', '{HASHED_PASSWORD_3}', 'bitsu@puls.ar', 0, NULL, 1)
        """)
    db.engine.execute("""INSERT INTO secondary_class_assoc VALUES (1, 1)""")


def unpopulate_db():
    "Unpopulate the database with test user information."
    db.engine.execute("DELETE FROM forums_posts_edit_history")
    db.engine.execute("DELETE FROM forums_posts")
    db.engine.execute("DELETE FROM forums_threads")
    db.engine.execute("DELETE FROM forums")
    db.engine.execute("DELETE FROM forums_categories")
    db.engine.execute("DELETE FROM secondary_class_assoc")
    db.engine.execute("DELETE FROM forums_permissions")
    db.engine.execute("DELETE FROM users_permissions")
    db.engine.execute("DELETE FROM sessions")
    db.engine.execute("DELETE FROM api_keys")
    db.engine.execute("DELETE FROM invites")
    db.engine.execute("DELETE FROM users")
    db.engine.execute("DELETE FROM user_classes")
    db.engine.execute("DELETE FROM secondary_classes")
    db.engine.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1")
    db.engine.execute("ALTER SEQUENCE user_classes_id_seq RESTART WITH 1")
    db.engine.execute("ALTER SEQUENCE secondary_classes_id_seq RESTART WITH 1")
