import flask
from voluptuous import Schema, Optional
from .. import bp
from ..models import Session
from pulsar import db, APIException, _404Exception
from pulsar.utils import (require_permission, validate_data, choose_user,
                          bool_get, many_to_dict)

app = flask.current_app


@bp.route('/sessions/<hash>', methods=['GET'])
@require_permission('view_sessions')
def view_session(hash):
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
           "active": true,
           "csrf_token": "d98a1a142ccae02be58ee64b",
           "hash": "abcdefghij",
           "ip": "127.0.0.1",
           "last_used": "1970-01-01T00:00:00.000001+00:00",
           "persistent": true,
           "user-agent": "curl/7.59.0"
         }
       }

    :>jsonarr boolean active: Whether or not the session is usable
    :>jsonarr string csrf_token: The csrf token of the session
    :>jsonarr string hash: The identification hash of the session
    :>jsonarr string ip: The last IP to access the session
    :>jsonarr string last_used: The timestamp at which the session was last accessed
    :>jsonarr boolean persistent: The persistence of the session
    :>jsonarr string user-agent: The last User Agent to access the session

    :statuscode 200: Successfully viewed session
    :statuscode 404: Session does not exist
    """
    session = Session.from_hash(hash, include_dead=True)
    if session:
        is_own_sess = session.user_id == flask.g.user.id
        if is_own_sess or flask.g.user.has_permission('view_sessions_others'):
            return flask.jsonify(session.to_dict())
    raise _404Exception(f'Session {hash}')


view_all_sessions_schema = Schema({
    Optional('include_dead', default=True): bool_get,
    })


@bp.route('/sessions', methods=['GET'])
@bp.route('/sessions/user/<int:user_id>', methods=['GET'])
@require_permission('view_sessions')
@validate_data(view_all_sessions_schema)
def view_all_sessions(include_dead, user_id=None):
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
             "active": true,
             "csrf_token": "d98a1a142ccae02be58ee64b",
             "hash": "abcdefghij",
             "ip": "127.0.0.1",
             "last_used": "1970-01-01T00:00:00.000001+00:00",
             "persistent": true,
             "user-agent": "curl/7.59.0"
           },
           {
             "active": true,
             "csrf_token": "a-long-csrf-token",
             "hash": "bcdefghijk",
             "ip": "127.0.0.1",
             "last_used": "1970-01-01T00:00:00.000001+00:00",
             "persistent": false,
             "user-agent": "curl/5.79.0"
           }
         ]
       }

    :query boolean include_dead: Whether or not to include dead sessions

    :>json list response: A list of sessions

    :>jsonarr boolean active: Whether or not the session is usable
    :>jsonarr string csrf_token: The csrf token of the session
    :>jsonarr string hash: The identification hash of the session
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
    return flask.jsonify(many_to_dict(sessions))


expire_sessions_schema = Schema({
    'identifier': str,
    }, required=True)


@bp.route('/sessions', methods=['DELETE'])
@require_permission('expire_sessions')
@validate_data(expire_sessions_schema)
def expire_session(identifier):
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

    :<json string identifier: The identification hash of the to-be expired session

    :>json string response: Status message of the response

    :statuscode 200: Successfully expired session
    :statuscode 400: Session is already expired
    :statuscode 404: Session does not exist
    """
    session = Session.from_hash(identifier, include_dead=True)
    if session:
        is_own_key = (session.user_id == flask.g.user.id)
        if is_own_key or flask.g.user.has_permission('expire_sessions_others'):
            if not session.active:
                raise APIException(f'Session {identifier} is already expired.')
            session.active = False
            db.session.commit()
            return flask.jsonify(f'Session {identifier} has been expired.')
    raise _404Exception(f'Session {identifier}')


@bp.route('/sessions/all', methods=['DELETE'])
@bp.route('/sessions/all/user/<int:user_id>', methods=['DELETE'])
@require_permission('expire_sessions')
def expire_all_sessions(user_id=None):
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

    :<json string identifier: The identification hash of the to-be expired session

    :>json string response: Status message of the response

    :statuscode 200: Successfully expired all sessions
    :statuscode 403: User does not have permission to expire sessions of another user
    :statuscode 404: User does not exist
    """
    user = choose_user(user_id, 'expire_sessions_others')
    Session.expire_all_of_user(user.id)
    db.session.commit()
    return flask.jsonify('All sessions have been expired.')
