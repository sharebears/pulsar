from typing import Optional as Optional_

import flask
from voluptuous import All, In, Length, Range, Schema

from pulsar import db
from pulsar.models import Forum, ForumPost, ForumThread
from pulsar.utils import require_permission, validate_data
from pulsar.validators import bool_get

from . import bp

app = flask.current_app


VIEW_FORUM_THREAD_SCHEMA = Schema({
    'page': All(int, Range(min=0, max=2147483648)),
    'limit': All(int, In((25, 50, 100))),
    'include_dead': bool_get
    })


@bp.route('/forums/threads/<int:id>', methods=['GET'])
@require_permission('view_forums')
@validate_data(VIEW_FORUM_THREAD_SCHEMA)
def view_thread(id: int,
                page: Optional_[int] = 1,
                limit: Optional_[int] = 50,
                include_dead: bool = False) -> flask.Response:
    """
    This endpoint allows users to view details about a forum and its threads.

    .. :quickref: ForumThread; View a forum thread.

    **Example request**:

    .. sourcecode:: http

       GET /forums/threads/1 HTTP/1.1
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

    :>json list response: A forum thread

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view thread
    :statuscode 404: Thread does not exist
    """
    thread = ForumThread.from_id(id, _404='Forum')
    thread.set_posts(
        page,
        limit,
        include_dead and flask.g.user.has_permission('modify_forum_posts_advanced'))
    return flask.jsonify(thread)


CREATE_THREAD_SCHEMA = Schema({  # TODO: Polls
    'topic': All(str, Length(max=150)),
    'forum_id': All(int, Range(min=0, max=2147483648)),
    }, required=True)


@bp.route('/forums/threads', methods=['POST'])
@require_permission('create_forum_threads')
@validate_data(CREATE_THREAD_SCHEMA)
def create_thread(topic: str,
                  forum_id: int) -> flask.Response:
    """
    This is the endpoint for forum thread creation. The ``modify_forum_threads``
    permission is required to access this endpoint.

    .. :quickref: ForumThread; Create a forum thread.

    **Example request**:

    .. sourcecode:: http
j
       POST /forums/threads HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "topic": "How do I get easy ration?",
         "forum_id": 4
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

    :>json list response: The newly created forum thread

    :statuscode 200: Creation successful
    :statuscode 400: Creation unsuccessful
    """
    forum = ForumThread.new(
        topic=topic,
        forum_id=forum_id,
        poster_id=flask.g.user.id)
    return flask.jsonify(forum)


MODIFY_FORUM_THREAD_SCHEMA = Schema({
    'topic': All(str, Length(max=150)),
    'forum_id': All(int, Range(min=0, max=2147483648)),
    'locked': bool_get,
    'sticky': bool_get,
    })


@bp.route('/forums/threads/<int:id>', methods=['PUT'])
@require_permission('modify_forum_threads')
@validate_data(MODIFY_FORUM_THREAD_SCHEMA)
def modify_thread(id: int,
                  topic: Optional_[str] = None,
                  forum_id: Optional_[int] = None,
                  locked: Optional_[bool] = None,
                  sticky: Optional_[bool] = None) -> flask.Response:
    """
    This is the endpoint for forum thread editing. The ``modify_forum_threads``
    permission is required to access this endpoint. The topic, forum_id,
    locked, and sticky attributes can be changed here.

    .. :quickref: ForumThread; Edit a forum thread.

    **Example request**:

    .. sourcecode:: http

       PUT /forums/threads/6 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "topic": "This does not contain typos.",
         "forum_id": 2,
         "locked": true,
         "sticky': false
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

    :>json dict response: The edited forum thread

    :statuscode 200: Editing successful
    :statuscode 400: Editing unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    thread = ForumThread.from_id(id, _404='Forum thread')
    if topic:
        thread.topic = topic
    if forum_id and Forum.is_valid(forum_id, error=True):
        thread.forum_id = forum_id
    if locked is not None:
        thread.locked = locked
    if sticky is not None:
        thread.sticky = sticky
    db.session.commit()
    return flask.jsonify(thread)


@bp.route('/forums/threads/<int:id>', methods=['DELETE'])
@require_permission('modify_forum_threads_advanced')
def delete_thread(id: int) -> flask.Response:
    """
    This is the endpoint for forum thread deletion . The ``modify_forum_threads_advanced``
    permission is required to access this endpoint. All posts in a deleted forum will also
    be deleted.

    .. :quickref: ForumThread; Delete a forum thread.

    **Example request**:

    .. sourcecode:: http

       DELETE /forums/threads2 HTTP/1.1
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

    :>json list response: The newly deleted forum thread

    :statuscode 200: Deletion successful
    :statuscode 400: Deletion unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    thread = ForumThread.from_id(id, _404='Forum thread')
    thread.deleted = True
    ForumPost.update_many(
        ids=ForumPost.get_ids_from_thread(thread.id),
        update={'deleted': True})
    return flask.jsonify(f'Forum thread {id} ({thread.topic}) has been deleted.')
