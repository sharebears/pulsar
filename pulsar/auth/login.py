import flask
from voluptuous import Schema, Optional
from . import bp
from .models import Session
from pulsar import db, _401Exception
from pulsar.utils import validate_data
from pulsar.users.models import User

app = flask.current_app

login_schema = Schema({
    'username': str,
    'password': str,
    Optional('persistent', default=False): bool,
}, required=True)


@bp.route('/login', methods=['POST'])
@validate_data(login_schema)
def login(username, password, persistent):
    """
    Login endpoint - generate a session and get a cookie. Yum!

    .. :quickref: Session; Generate a new session.

    **Example request**:

    .. sourcecode:: http

       POST /login HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "username": "lights",
         "password": "y-&~_Wbt7wjkUJdY<j-K",
         "persistent": true
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "csrf_token": "d98a1a142ccae02be58ee64b",
         "response": {
           "active": true,
           "csrf_token": "d98a1a142ccae02be58ee64b",
           "hash": "abcdefghij",
           "ip": "127.0.0.1",
           "last_used": "1970-01-01T00:00:00.000001+00:00",
           "persistent": true,
           "user-agent": "curl/7.59.0"
         }
       }

    :json username: Desired username: must start with an alphanumeric
        character and can only contain alphanumeric characters,
        underscores, hyphens, and periods.
    :json password: Desired password: must be 12+ characters and contain
        at least one letter, one number, and one special character.
    :json persistent: (Optional) Whether or not to persist the session.

    :>json dict response: A session, see sessions_

    .. _sessions:

    :statuscode 200: Login successful
    :statuscode 401: Login unsuccessful
    """
    user = User.from_username(username)
    if not user or not user.check_password(password):
        raise _401Exception(message='Invalid credentials.')

    session = Session.generate_session(
        user_id=user.id,
        ip=flask.request.remote_addr,
        user_agent=flask.request.user_agent.string,
        persistent=persistent)

    flask.session['user_id'] = user.id
    flask.session['session_hash'] = session.hash
    flask.session.permanent = persistent
    flask.session.modified = True
    return flask.jsonify(session.to_dict())
