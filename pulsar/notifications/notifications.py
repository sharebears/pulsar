# flake8:  noqa

from . import bp
from pulsar.forums.models import Forum, ForumThread


@bp.route('/notifications')
def view_notifications():
    """
    View all pending notifications for a user.
    """
    pass
