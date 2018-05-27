import flask

from pulsar.forums.models import ForumThread
from pulsar.utils import choose_user, require_permission

from . import bp


@bp.route('/notifications', methods=['GET'])
@bp.route('/notifications/user/<int:user_id>', methods=['GET'])
@require_permission('view_notifications')
def view_notifications(user_id=None):
    """
    View all pending notifications for a user. This includes thread subscriptions,
    collage notifications, torrent notifications, and inbox messages.
    """
    user = choose_user(user_id, 'view_notifications_others')
    return flask.jsonify({
        'forum_subscriptions': ForumThread.new_subscriptions(user.id),
        })


@bp.route('/subscriptions', methods=['GET'])
@bp.route('/subscriptions/user/<int:user_id>', methods=['GET'])
@require_permission('view_notifications')
def view_subscriptions(user_id=None):
    """
    View all pending subscriptions for a user.
    """
    user = choose_user(user_id, 'view_notifications_others')
    return flask.jsonify(ForumThread.new_subscriptions(user.id))
