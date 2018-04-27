import flask
from voluptuous import Schema, Optional
from .. import bp
from ..models import Session
from pulsar import db, _401Exception
from pulsar.utils import validate_data
from pulsar.users.models import User
from pulsar.users.schemas import user_schema

app = flask.current_app

login_schema = Schema({
    'username': str,
    'password': str,
    Optional('persistent', default=False): bool,
}, required=True)


@bp.route('/login', methods=['POST'])
@validate_data(login_schema)
def login(username, password, persistent):
    user = User.from_username(username)
    if not user or not user.check_password(password):
        raise _401Exception(message='Invalid credentials.')

    session = Session.generate_session(user.id, flask.request.remote_addr)
    db.session.add(session)
    db.session.commit()

    flask.session['user_id'] = user.id
    flask.session['session_hash'] = session.hash
    flask.session.permanent = persistent
    flask.session.modified = True
    return user_schema.jsonify(user)
