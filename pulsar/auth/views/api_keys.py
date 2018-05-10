import flask
from voluptuous import Schema, Optional
from .. import bp
from ..models import APIKey
from pulsar import db, APIException, _404Exception
from pulsar.utils import (require_permission, validate_data, choose_user,
                          bool_get, many_to_dict)
from pulsar.permissions.validators import permissions_list_of_user

app = flask.current_app


@bp.route('/api_keys/<hash>', methods=['GET'])
@require_permission('view_api_keys')
def view_api_key(hash):
    """
    View info of an API key. Requires the ``view_api_keys`` permission to view
    one's own API keys, and the ``view_api_keys_others`` permission to view
    the API keys of another user.

    .. :quickref: APIKey; View an API key.

    **Example request**:

    .. sourcecode:: http

       GET /api_keys/abcdefghij HTTP/1.1
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
           "hash": "abcdefghij",
           "ip": "127.0.0.1",
           "last_used": "1970-01-01T00:00:00.000001+00:00",
           "user-agent": "curl/7.59.0",
           "permissions": [
             "view_api_keys",
             "send_invites"
           ]
         }
       }

    :>jsonarr boolean active: Whether or not the API key is usable
    :>jsonarr string hash: The identification hash of the API key
    :>jsonarr string ip: The last IP to access the API key
    :>jsonarr string user-agent: The last User Agent to access the API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully viewed API key.
    :statuscode 404: API key does not exist.
    """
    api_key = APIKey.from_hash(hash, include_dead=True)
    if api_key:
        is_own_key = api_key.user_id == flask.g.user.id
        if is_own_key or flask.g.user.has_permission('view_api_keys_others'):
            return flask.jsonify(api_key.to_dict())
    raise _404Exception(f'API Key {hash}')


view_all_api_keys_schema = Schema({
    Optional('include_dead', default=True): bool_get,
    })


@bp.route('/api_keys', methods=['GET'])
@bp.route('/api_keys/user/<int:user_id>', methods=['GET'])
@require_permission('view_api_keys')
@validate_data(view_all_api_keys_schema)
def view_all_api_keys(include_dead, user_id=None):
    """
    View all API keys of a user. Requires the ``view_api_keys`` permission to view
    one's own API keys, and the ``view_api_keys_others`` permission to view
    the API keys of another user.

    .. :quickref: APIKey; View multiple API keys.

    **Example request**:

    .. sourcecode:: http

       GET /api_keys HTTP/1.1
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
             "hash": "abcdefghij",
             "ip": "127.0.0.1",
             "last_used": "1970-01-01T00:00:00.000001+00:00",
             "user-agent": "curl/7.59.0",
             "permissions": [
               "view_api_keys",
               "send_invites"
             ]
           }
         ]
       }

    :query boolean include_dead: Include dead (previously used) API keys

    :>json list response: A list of API keys

    :>jsonarr boolean active: Whether or not the API key is usable
    :>jsonarr string hash: The identification hash of the API key
    :>jsonarr string ip: The last IP to access the API key
    :>jsonarr string user-agent: The last User Agent to access the API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully viewed API keys
    :statuscode 403: User does not have permission to view user's API keys
    :statuscode 404: User does not exist
    """
    user = choose_user(user_id, 'view_api_keys_others')
    api_keys = APIKey.from_user(user.id, include_dead=include_dead)
    return flask.jsonify(many_to_dict(api_keys))


create_api_key_schema = Schema({
    Optional('permissions', default=[]): permissions_list_of_user,
    })


@bp.route('/api_keys', methods=['POST'])
@require_permission('create_api_keys')
@validate_data(create_api_key_schema)
def create_api_key(permissions):
    """
    Creates an API key for use. Requires the ``create_api_keys`` permission to
    create new API keys. Keys are unrecoverable after generation; if a key is lost,
    a new one will need to be generated.

    .. :quickref: APIKey; Create an API key.

    **Example request**:

    .. sourcecode:: http

       POST /api_keys HTTP/1.1
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
           "identifier": "abcdefghij",
           "key": "abcdefghijklmnopqrstuvwx",
           "permissions": [
             "view_api_keys",
             "send_invites"
           ]
         }
       }

    :>jsonarr string hash: The identification hash of the API key
    :>jsonarr string key: The full API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully created API key
    """
    raw_key, api_key = APIKey.generate_key(
        flask.g.user.id,
        flask.request.remote_addr,
        flask.request.user_agent.string,
        permissions
        )
    db.session.add(api_key)
    db.session.commit()

    return flask.jsonify({
        'identifier': api_key.hash,
        'key': raw_key,
        'permissions': permissions,
        })


revoke_api_key_schema = Schema({
    'identifier': str,
    }, required=True)


@bp.route('/api_keys', methods=['DELETE'])
@require_permission('revoke_api_keys')
@validate_data(revoke_api_key_schema)
def revoke_api_key(identifier):
    """
    Revokes an API key currently in use by the user. Requires the
    ``revoke_api_keys`` permission to revoke one's own API keys, and the
    ``revoke_api_keys_others`` permission to revoke the keys of other users.

    .. :quickref: APIKey; Revoke an API key.

    **Example request**:

    .. sourcecode:: http

       DELETE /api_keys HTTP/1.1
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
         "response": "API Key abcdefghij has been revoked."
       }

    :>jsonarr string hash: The identification hash of the API key
    :>jsonarr string key: The full API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully revoked API keys
    :statuscode 404: API key does not exist or user does not have permission
        to revoke the API key
    """
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
    """
    Revokes all API keys currently in use by the user. Requires the
    ``revoke_api_keys`` permission to revoke one's own API keys, and the
    ``revoke_api_keys_others`` permission to revoke the keys of other users.

    .. :quickref: APIKey; Revoke all API keys.

    **Example request**:

    .. sourcecode:: http

       DELETE /api_keys/all HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "All api keys have been revoked."
       }

    :>jsonarr string hash: The identification hash of the API key
    :>jsonarr string key: The full API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully revoked API keys
    :statuscode 403: User does not have permission to revoke API keys
    """
    user = choose_user(user_id, 'revoke_api_keys_others')
    APIKey.revoke_all_of_user(user.id)
    db.session.commit()
    return flask.jsonify('All api keys have been revoked.')
