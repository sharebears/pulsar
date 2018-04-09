import flask
from voluptuous import Schema, Optional
from . import bp
from ..models import Session
from ..schemas import session_schema, multiple_session_schema
from pulsar import db, APIException, _404Exception
from pulsar.utils import require_permission, validate_data, choose_user, bool_get

app = flask.current_app

view_all_sessions_schema = Schema({
    Optional('include_dead', default=True): bool_get,
    })

revoke_sessions_schema = Schema({
    'identifier': str,
    }, required=True)


@bp.route('/sessions/<hash>', methods=['GET'])
@require_permission('view_sessions')
def view_session(hash):
    session = Session.from_hash(hash, include_dead=True)
    if session:
        is_own_sess = session.user_id == flask.g.user.id
        if is_own_sess or flask.g.user.has_permission('view_sessions_others'):
            return session_schema.jsonify(session)
    raise _404Exception(f'Session {hash}')


@bp.route('/sessions', methods=['GET'])
@bp.route('/sessions/user/<int:user_id>', methods=['GET'])
@require_permission('view_sessions')
@validate_data(view_all_sessions_schema)
def view_all_sessions(include_dead, user_id=None):
    user = choose_user(user_id, 'view_sessions_others')
    sessions = user.sessions
    if not include_dead:
        sessions = [sess for sess in sessions if sess.active]
    return multiple_session_schema.jsonify(sessions)


@bp.route('/sessions', methods=['DELETE'])
@require_permission('revoke_sessions')
@validate_data(revoke_sessions_schema)
def revoke_session(identifier):
    session = Session.from_hash(identifier, include_dead=True)
    if session:
        is_own_key = (session.user_id == flask.g.user.id)
        if is_own_key or flask.g.user.has_permission('revoke_sessions_others'):
            if not session.active:
                raise APIException(f'Session {identifier} is already revoked.')
            session.active = False
            db.session.commit()
            return flask.jsonify(f'Session {identifier} has been revoked.')
    raise _404Exception(f'Session {identifier}')


@bp.route('/sessions/all', methods=['DELETE'])
@bp.route('/sessions/all/user/<int:user_id>', methods=['DELETE'])
@require_permission('revoke_sessions')
def revoke_all_sessions(user_id=None):
    user = choose_user(user_id, 'revoke_sessions_others')
    Session.expire_all_of_user(user.id)
    db.session.commit()
    return flask.jsonify('All sessions have been revoked.')
