from typing import Optional as Optional_

import flask
from voluptuous import All, Any, In, Length, Optional, Range, Schema

from pulsar import db
from pulsar.models import Forum, ForumCategory, ForumThread
from pulsar.utils import require_permission, validate_data
from pulsar.validators import bool_get

from . import bp

app = flask.current_app


VIEW_FORUM_SCHEMA = Schema({
    'page': All(int, Range(min=0, max=2147483648)),
    'limit': All(int, In((25, 50, 100))),
    'include_dead': bool_get
    })


@bp.route('/forums/<int:id>', methods=['GET'])
@require_permission('view_forums')
@validate_data(VIEW_FORUM_SCHEMA)
def view_forum(id: int,
               page: Optional_[int] = 1,
               limit: Optional_[int] = 50,
               include_dead: bool = False) -> flask.Response:
    """
    This endpoint allows users to view details about a forum and its threads.

    .. :quickref: Forum; View a forum.

    **Example request**:

    .. sourcecode:: http

       GET /forums/1 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           {
           }
         ]
       }

    :>json list response: A list of forums

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view forum
    :statuscode 404: Forum does not exist
    """
    forum = Forum.from_id(id, _404='Forum')
    forum.set_threads(
        page,
        limit,
        include_dead and flask.g.user.has_permission('modify_forum_threads_advanced'))
    return flask.jsonify(forum)


ADD_FORUM_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    'category_id': All(int, Range(min=0, max=2147483648)),
    Optional('description', default=None): Any(All(str, Length(max=1024)), None),
    Optional('position', default=0): All(int, Range(min=0, max=99999)),
    }, required=True)


@bp.route('/forums', methods=['POST'])
@require_permission('modify_forums')
@validate_data(ADD_FORUM_SCHEMA)
def add_forum(name: str,
              category_id: int,
              description: Optional_[str],
              position: int) -> flask.Response:
    """
    This is the endpoint for forum creation. The ``modify_forums`` permission
    is required to access this endpoint.

    .. :quickref: Forum; Create a forum.

    **Example request**:

    .. sourcecode:: http

       POST /forums HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "name": "Support",
         "description": "The place for confused share bears.",
         "position": 6
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json list response: The newly created forum

    :statuscode 200: Creation successful
    :statuscode 400: Creation unsuccessful
    """
    forum = Forum.new(
        name=name,
        category_id=category_id,
        description=description,
        position=position)
    return flask.jsonify(forum)


MODIFY_FORUM_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    'category_id': All(int, Range(min=0, max=2147483648)),
    'description': All(str, Length(max=1024)),
    'position': All(int, Range(min=0, max=99999)),
    })


@bp.route('/forums/<int:id>', methods=['PUT'])
@require_permission('modify_forums')
@validate_data(MODIFY_FORUM_SCHEMA)
def modify_forum(id: int,
                 name: Optional_[str] = None,
                 category_id: Optional_[int] = None,
                 description: Optional_[str] = None,
                 position: Optional_[int] = None) -> flask.Response:
    """
    This is the endpoint for forum editing. The ``modify_forums`` permission
    is required to access this endpoint. The name, category, description,
    and position of a forum can be changed here.

    .. :quickref: Forum; Edit a forum.

    **Example request**:

    .. sourcecode:: http

       PUT /forums/6 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "name": "Support",
         "description": "The place for **very** confused share bears.",
         "position": 99
       }


    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json dict response: The edited forum

    :statuscode 200: Editing successful
    :statuscode 400: Editing unsuccessful
    :statuscode 404: Forum does not exist
    """
    forum = Forum.from_id(id, _404='Forum')
    if name:
        forum.name = name
    if category_id and ForumCategory.is_valid(category_id, error=True):
        forum.category_id = category_id
    if description:
        forum.description = description
    if position is not None:
        forum.position = position
    db.session.commit()
    return flask.jsonify(forum)


@bp.route('/forums/<int:id>', methods=['DELETE'])
@require_permission('modify_forums')
def delete_forum(id: int) -> flask.Response:
    """
    This is the endpoint for forum deletion . The ``modify_forums`` permission
    is required to access this endpoint. All threads in a deleted forum will also
    be deleted.

    .. :quickref: Forum; Delete a forum.

    **Example request**:

    .. sourcecode:: http

       DELETE /forums/2 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json dict response: The newly deleted forum

    :statuscode 200: Deletion successful
    :statuscode 400: Deletion unsuccessful
    :statuscode 404: Forum does not exist
    """
    forum = Forum.from_id(id, _404='Forum')
    forum.deleted = True
    ForumThread.update_many(
        ids=ForumThread.get_ids_from_forum(forum.id),
        update={'deleted': True})
    return flask.jsonify(f'Forum {id} ({forum.name}) has been deleted.')
