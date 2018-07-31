from typing import List

import flask
from voluptuous import All, Length, Optional, Schema

from pulsar import APIException, _401Exception, db
from pulsar.users.models import APIKey, User
from pulsar.utils import choose_user, require_permission, validate_data
from pulsar.validators import BoolGET, PermissionsListOfUser

from . import bp

app = flask.current_app


@bp.route('/api_keys/<hash>', methods=['GET'])
@require_permission('view_api_keys')
def view_api_key(hash: str) -> flask.Response:
    """
    View info of an API key. Requires the ``view_api_keys`` permission to view
    one's own API keys, and the ``view_api_keys_others`` permission to view
    the API keys of another user.

    .. :quickref: APIKey; View an API key.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<APIKey>"
       }

    :>json dict response: An API key

    :statuscode 200: Successfully viewed API key.
    :statuscode 404: API key does not exist.
    """
    return flask.jsonify(APIKey.from_pk(
        hash, include_dead=True, _404=True, asrt='view_api_keys_others'))


VIEW_ALL_API_KEYS_SCHEMA = Schema({
    Optional('include_dead', default=True): BoolGET,
    })


@bp.route('/api_keys', methods=['GET'])
@bp.route('/api_keys/user/<int:user_id>', methods=['GET'])
@require_permission('view_api_keys')
@validate_data(VIEW_ALL_API_KEYS_SCHEMA)
def view_all_api_keys(include_dead: bool,
                      user_id: int = None) -> flask.Response:
    """
    View all API keys of a user. Requires the ``view_api_keys`` permission to view
    one's own API keys, and the ``view_api_keys_others`` permission to view
    the API keys of another user.

    .. :quickref: APIKey; View multiple API keys.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": [
            "<APIKey>",
            "<APIKey>"
         ]
       }

    :query boolean include_dead: Include dead (previously used) API keys

    :>json list response: A list of API keys

    :statuscode 200: Successfully viewed API keys
    :statuscode 403: User does not have permission to view user's API keys
    :statuscode 404: User does not exist
    """
    user = choose_user(user_id, 'view_api_keys_others')
    api_keys = APIKey.from_user(user.id, include_dead=include_dead)
    return flask.jsonify(api_keys)


CREATE_API_KEY_SCHEMA = Schema({
    'username': str,
    'password': str,
    'permissions': PermissionsListOfUser,
    })


@bp.route('/api_keys', methods=['POST'])
@validate_data(CREATE_API_KEY_SCHEMA)
def create_api_key(username: str = None,
                   password: str = None,
                   permissions: List[str] = None) -> flask.Response:
    """
    Creates an API key for use. Keys are unrecoverable after generation;
    if a key is lost, a new one will need to be generated.

    .. :quickref: APIKey; Create an API key.

    **Example request**:

    .. parsed-literal::

       POST /api_keys HTTP/1.1

       {
         "username": "lights",
         "password": "12345"
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": {
           "hash": "abcdefghij",
           "key": "abcdefghijklmnopqrstuvwx",
           "permissions": [
             "view_api_keys",
             "send_invites"
           ]
         }
       }

    :>jsonarr string hash: The identification id of the API key
    :>jsonarr string key: The full API key
    :>jsonarr list permissions: A list of permissions allowed to the API key,
        encoded as ``str``

    :statuscode 200: Successfully created API key
    """
    if not flask.g.user:
        if username is not None:
            flask.g.user = User.from_username(username)
        if not flask.g.user or not flask.g.user.check_password(password):
            raise _401Exception('Invalid credentials.')

    raw_key, api_key = APIKey.new(
        flask.g.user.id,
        flask.request.remote_addr,
        flask.request.user_agent.string,
        permissions)
    return flask.jsonify({
        'hash': api_key.hash,
        'key': raw_key,
        'permissions': permissions,
        })


REVOKE_API_KEY_SCHEMA = Schema({
    'hash': All(str, Length(min=10, max=10)),
    }, required=True)


@bp.route('/api_keys', methods=['DELETE'])
@require_permission('revoke_api_keys')
@validate_data(REVOKE_API_KEY_SCHEMA)
def revoke_api_key(hash: int) -> flask.Response:
    """
    Revokes an API key currently in use by the user. Requires the
    ``revoke_api_keys`` permission to revoke one's own API keys, and the
    ``revoke_api_keys_others`` permission to revoke the keys of other users.

    .. :quickref: APIKey; Revoke an API key.

    **Example request**:

    .. parsed-literal::

       DELETE /api_keys HTTP/1.1

       {
         "hash": "abcdefghij"
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "API Key abcdefghij has been revoked."
       }

    :<json str hash: The hash of the API key

    :statuscode 200: Successfully revoked API keys
    :statuscode 404: API key does not exist or user does not have permission
        to revoke the API key
    """
    api_key = APIKey.from_pk(
        hash, include_dead=True, _404=True, asrt='revoke_api_keys_others')
    if api_key.revoked:
        raise APIException(f'APIKey {hash} is already revoked.')
    api_key.revoked = True
    db.session.commit()
    return flask.jsonify(f'APIKey {hash} has been revoked.')


@bp.route('/api_keys/all', methods=['DELETE'])
@bp.route('/api_keys/all/user/<int:user_id>', methods=['DELETE'])
@require_permission('revoke_api_keys')
def revoke_all_api_keys(user_id: int = None) -> flask.Response:
    """
    Revokes all API keys currently in use by the user. Requires the
    ``revoke_api_keys`` permission to revoke one's own API keys, and the
    ``revoke_api_keys_others`` permission to revoke the keys of other users.

    .. :quickref: APIKey; Revoke all API keys.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "All api keys have been revoked."
       }

    :statuscode 200: Successfully revoked API keys
    :statuscode 403: User does not have permission to revoke API keys
    """
    user = choose_user(user_id, 'revoke_api_keys_others')
    APIKey.update_many(
        pks=APIKey.hashes_from_user(user.id),
        update={'revoked': True})
    db.session.commit()
    return flask.jsonify('All api keys have been revoked.')
