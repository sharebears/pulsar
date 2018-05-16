from typing import List, Optional as TOptional

import flask
from voluptuous import All, Length, Optional, Schema

from pulsar import APIException, db
from pulsar.models import APIKey
from pulsar.utils import choose_user, require_permission, validate_data
from pulsar.validators import bool_get, permissions_list_of_user

from . import bp

app = flask.current_app


@bp.route('/api_keys/<id>', methods=['GET'])
@require_permission('view_api_keys')
def view_api_key(id: str) -> 'flask.Response':
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
           "revoked": false,
           "id": "abcdefghij",
           "ip": "127.0.0.1",
           "last_used": "1970-01-01T00:00:00.000001+00:00",
           "user-agent": "curl/7.59.0",
           "permissions": [
             "view_api_keys",
             "send_invites"
           ]
         }
       }

    :>jsonarr boolean revoked: Whether or not the API key is revoked
    :>jsonarr string id: The identification id of the API key
    :>jsonarr string ip: The last IP to access the API key
    :>jsonarr string user-agent: The last User Agent to access the API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully viewed API key.
    :statuscode 404: API key does not exist.
    """
    return flask.jsonify(APIKey.from_id(
        id, include_dead=True, _404='API Key', asrt='view_api_keys_others'))


view_all_api_keys_schema = Schema({
    Optional('include_dead', default=True): bool_get,
    })


@bp.route('/api_keys', methods=['GET'])
@bp.route('/api_keys/user/<int:user_id>', methods=['GET'])
@require_permission('view_api_keys')
@validate_data(view_all_api_keys_schema)
def view_all_api_keys(include_dead: bool,
                      user_id: TOptional[int] = None) -> 'flask.Response':
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
             "revoked": false,
             "id": "abcdefghij",
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

    :>jsonarr boolean revoked: Whether or not the API key is revoked
    :>jsonarr string id: The identification id of the API key
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
    return flask.jsonify(api_keys)


create_api_key_schema = Schema({
    Optional('permissions', default=[]): permissions_list_of_user,
    })


@bp.route('/api_keys', methods=['POST'])
@require_permission('create_api_keys')
@validate_data(create_api_key_schema)
def create_api_key(permissions: List[str]) -> 'flask.Response':
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

    :>jsonarr string id: The identification id of the API key
    :>jsonarr string key: The full API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully created API key
    """
    raw_key, api_key = APIKey.new(
        flask.g.user.id,
        flask.request.remote_addr,
        flask.request.user_agent.string,
        permissions)
    return flask.jsonify({
        'id': api_key.id,
        'key': raw_key,
        'permissions': permissions,
        })


revoke_api_key_schema = Schema({
    'id': All(str, Length(min=10, max=10)),
    }, required=True)


@bp.route('/api_keys', methods=['DELETE'])
@require_permission('revoke_api_keys')
@validate_data(revoke_api_key_schema)
def revoke_api_key(id: int) -> 'flask.Response':
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
         "id": "abcdefghij"
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

    :<json str id: The ID of the API key

    :>jsonarr string id: The ID of the API key
    :>jsonarr string key: The full API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully revoked API keys
    :statuscode 404: API key does not exist or user does not have permission
        to revoke the API key
    """
    api_key = APIKey.from_id(
        id, include_dead=True, _404='API Key', asrt='revoke_api_keys_others')
    if api_key.revoked:
        raise APIException(f'API Key {id} is already revoked.')
    api_key.revoked = True
    db.session.commit()
    return flask.jsonify(f'API Key {id} has been revoked.')


@bp.route('/api_keys/all', methods=['DELETE'])
@bp.route('/api_keys/all/user/<int:user_id>', methods=['DELETE'])
@require_permission('revoke_api_keys')
def revoke_all_api_keys(user_id: TOptional[int] = None) -> 'flask.Response':
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

    :>jsonarr string id: The identification id of the API key
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
