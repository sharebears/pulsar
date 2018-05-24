from datetime import datetime

import flask
import pytz
from voluptuous import All, Length, Range, Schema

from pulsar import APIException, db
from pulsar.forums.models import (ForumPost, ForumPostEditHistory, ForumThread,
                                  ForumThreadSubscription)
from pulsar.utils import assert_user, require_permission, validate_data

from . import bp

app = flask.current_app


@bp.route('/forums/posts/<int:id>', methods=['GET'])
@require_permission('view_forums')
def view_post(id: int) -> flask.Response:
    """
    This endpoint allows users to view a forum post.

    .. :quickref: ForumPost; View a forum post.

    **Example request**:

    .. sourcecode:: http

       GET /forums/posts/1 HTTP/1.1
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

    :>json list response: A forum post

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view post
    :statuscode 404: Post does not exist
    """
    return flask.jsonify(ForumPost.from_id(
        id,
        _404=True,
        include_dead=flask.g.user.has_permission('modify_forum_posts_advanced')))


CREATE_FORUM_POST_SCHEMA = Schema({
    'contents': All(str, Length(max=256000)),
    'thread_id': All(int, Range(min=0, max=2147483648)),
    }, required=True)


@bp.route('/forums/posts', methods=['POST'])
@require_permission('create_forum_posts')
@validate_data(CREATE_FORUM_POST_SCHEMA)
def create_post(contents: str,
                thread_id: int) -> flask.Response:
    """
    This is the endpoint for forum posting. The ``modify_forum_posts``
    permission is required to access this endpoint.

    .. :quickref: ForumPost; Create a forum post.

    **Example request**:

    .. sourcecode:: http

       POST /forums/posts HTTP/1.1
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

    :>json list response: The newly created forum post

    :statuscode 200: Creation successful
    :statuscode 400: Creation unsuccessful
    """
    thread = ForumThread.from_id(thread_id, _404=True)
    if thread.locked and not flask.g.user.has_permission('forums_post_in_locked_threads'):
        raise APIException('You cannot post in a locked thread.')
    thread_last_post = thread.last_post
    if (thread_last_post
            and thread_last_post.poster_id == flask.g.user.id
            and not flask.g.user.has_permission('forum_double_post')):
        if len(thread_last_post.contents) + len(contents) > 255997:
            raise APIException('Post could not be merged into previous post '
                               '(must be <256,000 characters combined).')
        return modify_post(
            id=thread_last_post.id,
            contents=f'{thread_last_post.contents}\n\n\n{contents}',
            skip_validation=True)

    post = ForumPost.new(
        thread_id=thread_id,
        poster_id=flask.g.user.id,
        contents=contents)
    ForumThreadSubscription.clear_cache_keys(thread_id=thread_id)
    return flask.jsonify(post)


MODIFY_FORUM_POST_SCHEMA = Schema({
    'sticky': bool,
    'contents': All(str, Length(max=250000)),
    })


@bp.route('/forums/posts/<int:id>', methods=['PUT'])
@require_permission('create_forum_posts')
@validate_data(MODIFY_FORUM_POST_SCHEMA)
def modify_post(id: int,
                sticky: bool = None,
                contents: str = None) -> flask.Response:
    """
    This is the endpoint for forum post editing. The ``modify_forum_posts``
    permission is required to access this endpoint. Posts can be marked
    sticky with this endpoint.

    .. :quickref: ForumThread; Edit a forum post.

    **Example request**:

    .. sourcecode:: http

       PUT /forums/posts/6 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "sticky": true
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

    :>json dict response: The modified forum post

    :statuscode 200: Modification successful
    :statuscode 400: Modification unsuccessful
    :statuscode 404: Forum post does not exist
    """
    post = ForumPost.from_id(id, _404=True)
    assert_user(post.poster_id, 'modify_forum_posts')
    thread = ForumThread.from_id(post.thread_id)
    if not thread:
        raise APIException(f'ForumPost {id} does not exist.')
    if thread.locked and not flask.g.user.has_permission('modify_forum_posts'):
        raise APIException('You cannot modify posts in a locked thread.')
    if contents is not None:
        ForumPostEditHistory.new(
            post_id=post.id,
            editor_id=post.edited_user_id or post.poster_id,
            contents=post.contents,
            time=datetime.utcnow().replace(tzinfo=pytz.utc))
        post.contents = contents
        post.edited_user_id = flask.g.user.id
        post.edited_time = datetime.utcnow().replace(tzinfo=pytz.utc)
    if flask.g.user.has_permission('modify_forum_posts'):
        if sticky is not None:
            post.sticky = sticky
    db.session.commit()
    return flask.jsonify(post)


@bp.route('/forums/posts/<int:id>', methods=['DELETE'])
@require_permission('modify_forum_posts_advanced')
def delete_post(id: int) -> flask.Response:
    """
    This is the endpoint for forum post deletion . The ``modify_forum_posts_advanced``
    permission is required to access this endpoint. All posts in a deleted forum will also
    be deleted.

    .. :quickref: ForumPost; Delete a forum post.

    **Example request**:

    .. sourcecode:: http

       DELETE /forums/posts/2 HTTP/1.1
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

    :>json list response: The newly deleted forum post

    :statuscode 200: Deletion successful
    :statuscode 400: Deletion unsuccessful
    :statuscode 404: Forum post does not exist
    """
    post = ForumPost.from_id(id, _404=True)
    post.deleted = True
    db.session.commit()
    return flask.jsonify(f'ForumPost {id} has been deleted.')
