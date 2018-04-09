import flask
from voluptuous import Schema, Optional
from . import bp
from ..models import APIKey, APIPermission
from ..schemas import api_key_schema, multiple_api_key_schema
from pulsar import db, APIException, _404Exception
from pulsar.utils import (require_permission, validate_data, choose_user,
                          bool_get, permissions_list)

app = flask.current_app

view_all_api_keys_schema = Schema({
    Optional('include_dead', default=True): bool_get,
    })

create_api_key_schema = Schema({
    Optional('permissions', default=[]): permissions_list,
    })

revoke_api_key_schema = Schema({
    'identifier': str,
    }, required=True)


@bp.route('/api_keys/<hash>', methods=['GET'])
@require_permission('view_api_keys')
def view_api_key(hash):
    api_key = APIKey.from_hash(hash, include_dead=True)
    if api_key:
        is_own_key = api_key.user_id == flask.g.user.id
        if is_own_key or flask.g.user.has_permission('view_api_keys_others'):
            return api_key_schema.jsonify(api_key)
    raise _404Exception(f'API Key {hash}')


@bp.route('/api_keys', methods=['GET'])
@bp.route('/api_keys/user/<int:user_id>', methods=['GET'])
@require_permission('view_api_keys')
@validate_data(view_all_api_keys_schema)
def view_all_api_keys(include_dead, user_id=None):
    user = choose_user(user_id, 'view_api_keys_others')
    api_keys = user.api_keys
    if not include_dead:
        api_keys = [key for key in api_keys if key.active]
    return multiple_api_key_schema.jsonify(api_keys)


@bp.route('/api_keys', methods=['POST'])
@require_permission('create_api_keys')
@validate_data(create_api_key_schema)
def create_api_key(permissions):
    """
    Keys are hashed and salted and cannot be recovered after generation.
    """
    raw_key, api_key = APIKey.generate_key(
        flask.g.user.id, flask.request.remote_addr)
    db.session.add(api_key)
    for perm in permissions:
        permission = APIPermission(
            api_key_hash=api_key.hash,
            permission=perm,
            )
        db.session.add(permission)

    db.session.commit()
    return flask.jsonify({
        'identifier': api_key.hash,
        'key': raw_key,
        'permissions': permissions,
        })


@bp.route('/api_keys', methods=['DELETE'])
@require_permission('revoke_api_keys')
@validate_data(revoke_api_key_schema)
def revoke_api_key(identifier):
    api_key = APIKey.from_hash(identifier, include_dead=True)
    if api_key:
        is_own_key = (api_key.user_id == flask.g.user.id)
        if is_own_key or flask.g.user.has_permission('revoke_api_keys_others'):
            if not api_key.active:
                raise APIException(f'API Key {identifier} is already revoked.')
            api_key.active = False
            db.session.commit()
            return flask.jsonify(f'API Key {identifier} has been revoked.')
    raise _404Exception(f'API Key {identifier}')


@bp.route('/api_keys/all', methods=['DELETE'])
@bp.route('/api_keys/all/user/<int:user_id>', methods=['DELETE'])
@require_permission('revoke_api_keys')
def revoke_all_api_keys(user_id=None):
    user = choose_user(user_id, 'revoke_api_keys_others')
    APIKey.revoke_all_of_user(user.id)
    db.session.commit()
    return flask.jsonify('All api keys have been revoked.')
