from typing import Optional as Optional_

import flask
from voluptuous import All, Length, Optional, Schema

from pulsar import APIException, _401Exception, db
from pulsar.models import Session, User
from pulsar.utils import choose_user, require_permission, validate_data
from pulsar.validators import bool_get

from . import bp

app = flask.current_app


@bp.route('/sessions/<id>', methods=['GET'])
@require_permission('view_sessions')
def view_session(id: int) -> flask.Response:
    """
    View info related to a user session. Requires the ``view_sessions`` permission
    to view one's own sessions, and the ``view_sessions_others`` permission to view
    the sessions of another user.

    .. :quickref: Session; View a session.

    **Example request**:

    .. sourcecode:: http

       POST /sessions/abcdefghij HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "expired": true,
           "csrf_token": "d98a1a142ccae02be58ee64b",
           "id": "abcdefghij",
           "ip": "127.0.0.1",
           "last_used": "1970-01-01T00:00:00.000001+00:00",
           "persistent": true,
           "user-agent": "curl/7.59.0"
         }
       }

    :>jsonarr boolean expired: Whether or not the session is expired
    :>jsonarr string csrf_token: The csrf token of the session
    :>jsonarr string id: The identification id of the session
    :>jsonarr string ip: The last IP to access the session
    :>jsonarr string last_used: The timestamp at which the session was last accessed
    :>jsonarr boolean persistent: The persistence of the session
    :>jsonarr string user-agent: The last User Agent to access the session

    :statuscode 200: Successfully viewed session
    :statuscode 404: Session does not exist
    """
    return flask.jsonify(Session.from_id(
        id, include_dead=True, _404='Session', asrt='view_sessions_others'))


VIEW_ALL_SESSIONS_SCHEMA = Schema({
    Optional('include_dead', default=True): bool_get,
    })


@bp.route('/sessions', methods=['GET'])
@bp.route('/sessions/user/<int:user_id>', methods=['GET'])
@require_permission('view_sessions')
@validate_data(VIEW_ALL_SESSIONS_SCHEMA)
def view_all_sessions(include_dead: bool,
                      user_id: Optional_[int] = None) -> flask.Response:
    """
    View all sessions of a user. Requires the ``view_sessions`` permission
    to view one's own sessions, and the ``view_sessions_others`` permission to view
    the sessions of another user. Dead sessions can be included via an optional param.

    .. :quickref: Session; View multiple sessions.

    **Example request**:

    .. sourcecode:: http

       POST /sessions HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           {
             "expired": false,
             "csrf_token": "d98a1a142ccae02be58ee64b",
             "id": "abcdefghij",
             "ip": "127.0.0.1",
             "last_used": "1970-01-01T00:00:00.000001+00:00",
             "persistent": true,
             "user-agent": "curl/7.59.0"
           },
           {
             "expired": false,
             "csrf_token": "a-long-csrf-token",
             "id": "bcdefghijk",
             "ip": "127.0.0.1",
             "last_used": "1970-01-01T00:00:00.000001+00:00",
             "persistent": false,
             "user-agent": "curl/5.79.0"
           }
         ]
       }

    :query boolean include_dead: Whether or not to include dead sessions

    :>json list response: A list of sessions

    :>jsonarr boolean expired: Whether or not the session is expired
    :>jsonarr string csrf_token: The csrf token of the session
    :>jsonarr string id: The identification id of the session
    :>jsonarr string ip: The last IP to access the session
    :>jsonarr string last_used: The timestamp at which the session was last accessed
    :>jsonarr boolean persistent: The persistence of the session
    :>jsonarr string user-agent: The last User Agent to access the session

    :statuscode 200: Successfully viewed sessions
    :statuscode 403: User does not have permission to view sessions of another user
    :statuscode 404: User does not exist
    """
    user = choose_user(user_id, 'view_sessions_others')
    sessions = Session.from_user(user.id, include_dead=include_dead)
    return flask.jsonify(sessions)


CREATE_SESSION_SCHEMA = Schema({
    'username': All(str, Length(max=32)),
    'password': str,
    Optional('persistent', default=False): bool,
}, required=True)


@bp.route('/sessions', methods=['POST'])
@validate_data(CREATE_SESSION_SCHEMA)
def create_session(username: str, password: str, persistent: bool) -> flask.Response:
    """
    Login endpoint - generate a session and get a cookie. Yum!

    .. :quickref: Session; Generate a new session.

    **Example request**:

    .. sourcecode:: http

       POST /session HTTP/1.1
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
           "expired": false,
           "csrf_token": "d98a1a142ccae02be58ee64b",
           "id": "abcdefghij",
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
    flask.g.user = user

    session = Session.new(
        user_id=user.id,
        ip=flask.request.remote_addr,
        user_agent=flask.request.user_agent.string,
        persistent=persistent)

    flask.session['user_id'] = user.id
    flask.session['session_id'] = session.id
    flask.session.permanent = persistent
    flask.session.modified = True
    return flask.jsonify(session)


EXPIRE_SESSIONS_SCHEMA = Schema({
    'id': All(str, Length(min=10, max=10)),
    }, required=True)


@bp.route('/sessions', methods=['DELETE'])
@require_permission('expire_sessions')
@validate_data(EXPIRE_SESSIONS_SCHEMA)
def expire_session(id: int) -> flask.Response:
    """
    Revoke a user's session. Requires the ``expire_sessions`` permission to expire
    one's own sessions, and the ``expire_sessions_others`` permission to expire
    the sessions of another user.

    .. :quickref: Session; Revoke a session.

    **Example request**:

    .. sourcecode:: http

       DELETE /sessions HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "identifier": "abcdefghij"
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "Session abcdefghij has been expired."
       }

    :<json string identifier: The identification id of the to-be expired session

    :>json string response: Status message of the response

    :statuscode 200: Successfully expired session
    :statuscode 400: Session is already expired
    :statuscode 404: Session does not exist
    """
    session = Session.from_id(
        id, include_dead=True, _404='Session', asrt='expire_sessions_others')
    if session.expired:
        raise APIException(f'Session {id} is already expired.')
    session.expired = True
    db.session.commit()
    return flask.jsonify(f'Session {id} has been expired.')


@bp.route('/sessions/all', methods=['DELETE'])
@bp.route('/sessions/all/user/<int:user_id>', methods=['DELETE'])
@require_permission('expire_sessions')
def expire_all_sessions(user_id: Optional_[int] = None) -> flask.Response:
    """
    Revoke all sessions of a user. Requires the ``expire_sessions`` permission to
    expire one's own sessions, and the ``expire_sessions_others`` permission to expire
    the sessions of another user.

    .. :quickref: Session; Revoke multiple sessions.

    **Example request**:

    .. sourcecode:: http

       DELETE /sessions/all HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "All sessions have been expired."
       }

    :<json string identifier: The identification id of the to-be expired session

    :>json string response: Status message of the response

    :statuscode 200: Successfully expired all sessions
    :statuscode 403: User does not have permission to expire sessions of another user
    :statuscode 404: User does not exist
    """
    user = choose_user(user_id, 'expire_sessions_others')
    Session.update_many(
        ids=Session.ids_from_user(user.id),
        update={'expired': True})
    db.session.commit()
    return flask.jsonify('All sessions have been expired.')
