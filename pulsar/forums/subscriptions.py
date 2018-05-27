import flask

from pulsar import APIException, db
from pulsar.forums.models import (Forum, ForumThread, ForumSubscription, ForumThreadSubscription)
from pulsar.utils import require_permission

from . import bp


@bp.route('/forums/threads/<int:thread_id>/subscribe', methods=['POST', 'DELETE'])
@require_permission('modify_forum_subscriptions')
def alter_thread_subscription(thread_id: int) -> flask.Response:
    """
    This is the endpoint for forum thread subscription. The ``modify_forum_subscriptions``
    permission is required to access this endpoint. A POST request creates a subscription,
    whereas a DELETE request removes a subscription.

    .. :quickref: ForumThread; Subscribe to a forum thread.

    **Example request**:

    .. sourcecode:: http

       PUT /forums/threads/2/subscribe HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "Successfully subscribed to thread 2."
       }

    :>json str response: Success or failure message

    :statuscode 200: Subscription alteration successful
    :statuscode 400: Subscription alteration unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    thread = ForumThread.from_pk(thread_id, _404=True)
    subscription = ForumThreadSubscription.from_attrs(
        user_id=flask.g.user.id,
        thread_id=thread.id)
    if flask.request.method == 'POST':
        if subscription:
            raise APIException(f'You are already subscribed to thread {thread_id}.')
        ForumThreadSubscription.new(
            user_id=flask.g.user.id,
            thread_id=thread_id)
        return flask.jsonify(f'Successfully subscribed to thread {thread_id}.')
    else:  # method = DELETE
        if not subscription:
            raise APIException(f'You are not subscribed to thread {thread_id}.')
        db.session.delete(subscription)
        db.session.commit()
        return flask.jsonify(f'Successfully unsubscribed from thread {thread_id}.')


@bp.route('/forums/<int:forum_id>/subscribe', methods=['POST', 'DELETE'])
@require_permission('modify_forum_subscriptions')
def alter_forum_subscription(forum_id: int) -> flask.Response:
    """
    This is the endpoint for forum subscription. The ``modify_forum_subscriptions``
    permission is required to access this endpoint. A POST request creates a subscription,
    whereas a DELETE request removes a subscription.

    .. :quickref: Forum; Subscribe to a forum.

    **Example request**:

    .. sourcecode:: http

       PUT /forums/2/subscribe HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": "Successfully subscribed to forum 2."
       }

    :>json str response: Success or failure message

    :statuscode 200: Subscription alteration successful
    :statuscode 400: Subscription alteration unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    forum = Forum.from_pk(forum_id, _404=True)
    subscription = ForumSubscription.from_attrs(
        user_id=flask.g.user.id,
        forum_id=forum.id)
    if flask.request.method == 'POST':
        if subscription:
            raise APIException(f'You are already subscribed to forum {forum_id}.')
        ForumSubscription.new(
            user_id=flask.g.user.id,
            forum_id=forum_id)
        return flask.jsonify(f'Successfully subscribed to forum {forum_id}.')
    else:  # method = DELETE
        if not subscription:
            raise APIException(f'You are not subscribed to forum {forum_id}.')
        db.session.delete(subscription)
        db.session.commit()
        return flask.jsonify(f'Successfully unsubscribed from forum {forum_id}.')


@bp.route('/forums/subscriptions', methods=['GET'])
@require_permission('view_forums')
def view_forum_subscriptions() -> flask.Response:
    return flask.jsonify({  # type: ignore
        'forum_subscriptions': Forum.from_subscribed_user(flask.g.user.id),
        'thread_subscriptions': ForumThread.from_subscribed_user(flask.g.user.id),
        })
